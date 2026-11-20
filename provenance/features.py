"""Feature extraction shared by source and binary paths.

Features are typed strings so that source-side and binary-side extraction land
in the same vocabulary:

    s:<text>   string literal (normalized)
    c:<int>    integer constant (only values that survive as immediates)
    i:<name>   imported / called library symbol
    f:<name>   function symbol name (only visible in unstripped binaries)
    w:<hash>   winnowed k-gram of normalized source tokens (source-only)
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

MIN_STRING_LEN = 6
MIN_CONSTANT = 256
WINNOW_K = 12
WINNOW_W = 8

C_KEYWORDS = frozenset(
    """auto break case char const continue default do double else enum extern
    float for goto if inline int long register restrict return short signed
    sizeof static struct switch typedef union unsigned void volatile while
    _Bool size_t uint8_t uint16_t uint32_t uint64_t int32_t int64_t NULL""".split()
)

LIBC_SYMBOLS = frozenset(
    """printf fprintf snprintf sprintf puts fputs putchar fopen fclose fread
    fwrite fgets fseek ftell malloc calloc realloc free memcpy memset memcmp
    memmove strlen strcmp strncmp strcpy strncpy strcat strchr strrchr strstr
    strtok strtol strtoul atoi qsort bsearch exit abort time clock rand srand
    getenv isalpha isdigit isspace toupper tolower sqrt pow fabs""".split()
)

_STRING_RE = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
_COMMENT_RE = re.compile(r"/\*.*?\*/|//[^\n]*", re.S)
_INT_RE = re.compile(r"\b(0[xX][0-9a-fA-F]+|\d+)[uUlL]*\b")
_TOKEN_RE = re.compile(r"[A-Za-z_]\w*|0[xX][0-9a-fA-F]+|\d+|\S")
_CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
_FUNC_DEF_RE = re.compile(r"^[A-Za-z_][\w\s\*]*?\b([A-Za-z_]\w*)\s*\([^;{]*\)\s*\{", re.M)
_FMT_RE = re.compile(r"%[-+ #0]*\d*(?:\.\d+)?[hlLqjzt]*[diouxXeEfgGcsp%]")


def normalize_string(raw: str) -> str | None:
    """Normalize a literal so source and binary forms compare equal.

    Compilers rewrite ``printf("x\\n")`` to ``puts("x")`` and keep format
    strings verbatim otherwise, so trailing newlines and format directives are
    dropped and whitespace is collapsed.
    """
    s = raw.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"').replace("\\\\", "\\")
    s = _FMT_RE.sub(" ", s)
    s = " ".join(s.split())
    if len(s) < MIN_STRING_LEN or not any(ch.isalpha() for ch in s):
        return None
    return s.lower()


def _constant_ok(v: int) -> bool:
    return v >= MIN_CONSTANT and v not in (0xFFFFFFFF, 0xFFFFFFFFFFFFFFFF)


@dataclass
class FeatureSet:
    features: set[str] = field(default_factory=set)
    kind: str = "source"

    def by_type(self, prefix: str) -> set[str]:
        return {f for f in self.features if f.startswith(prefix)}


def _winnow(tokens: list[str], k: int = WINNOW_K, w: int = WINNOW_W) -> set[str]:
    if len(tokens) < k:
        return set()
    grams = [
        int.from_bytes(hashlib.blake2b(" ".join(tokens[i : i + k]).encode(), digest_size=8).digest(), "big")
        for i in range(len(tokens) - k + 1)
    ]
    picked: set[str] = set()
    for i in range(max(1, len(grams) - w + 1)):
        window = grams[i : i + w]
        picked.add(f"w:{min(window):016x}")
    return picked


def normalized_source_tokens(code: str) -> list[str]:
    """Token stream with identifiers/literals abstracted (rename-resistant)."""
    code = _COMMENT_RE.sub(" ", code)
    code = _STRING_RE.sub(' "STR" ', code)
    out = []
    for tok in _TOKEN_RE.findall(code):
        if tok in C_KEYWORDS or tok in LIBC_SYMBOLS:
            out.append(tok)
        elif tok[0].isalpha() or tok[0] == "_":
            out.append("ID")
        elif tok[0].isdigit():
            out.append("NUM")
        else:
            out.append(tok)
    return out


def extract_source(code: str, include_winnow: bool = True) -> FeatureSet:
    stripped = _COMMENT_RE.sub(" ", code)
    feats: set[str] = set()
    for lit in _STRING_RE.findall(stripped):
        n = normalize_string(lit)
        if n:
            feats.add("s:" + n)
    no_strings = _STRING_RE.sub('""', stripped)
    for m in _INT_RE.findall(no_strings):
        v = int(m, 16) if m[:2].lower() == "0x" else int(m, 10)
        if _constant_ok(v):
            feats.add(f"c:{v}")
    for name in _CALL_RE.findall(no_strings):
        if name in LIBC_SYMBOLS:
            feats.add("i:" + _IMPORT_ALIASES.get(name, name))
    for name in _FUNC_DEF_RE.findall(no_strings):
        if name not in C_KEYWORDS and name != "main":
            feats.add("f:" + name)
    if include_winnow:
        feats |= _winnow(normalized_source_tokens(code))
    return FeatureSet(feats, "source")


def _printable_strings(data: bytes, min_len: int = 4) -> list[str]:
    return [m.decode("ascii", "ignore") for m in re.findall(rb"[\x20-\x7e\t]{%d,}" % min_len, data)]


_IMM_RE = re.compile(r"\$0x([0-9a-f]+)")

# The compiler freely swaps these (printf("x\n") -> puts("x"), etc.).
_IMPORT_ALIASES = {"puts": "printf", "putchar": "printf", "fputs": "fprintf", "fwrite": "fprintf", "sprintf": "snprintf"}


def _tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"required binutils tool not found: {name}")
    return path


def extract_binary(path: str | Path) -> FeatureSet:
    """Extract source-recoverable features from an ELF binary.

    Uses only static inspection (no execution). PE/Mach-O are out of scope for
    the vertical slice.
    """
    path = Path(path)
    data = path.read_bytes()
    if data[:4] != b"\x7fELF":
        raise ValueError(f"{path} is not an ELF binary; only ELF is supported in this slice")
    feats: set[str] = set()
    for s in _printable_strings(data):
        n = normalize_string(s)
        if n:
            feats.add("s:" + n)
    dis = subprocess.run(
        [_tool("objdump"), "-d", "--no-show-raw-insn", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    for line in dis.splitlines():
        if "\t" not in line:
            continue
        ins = line.split("\t", 1)[1]
        for hx in _IMM_RE.findall(ins):
            v = int(hx, 16)
            if _constant_ok(v) and v < 1 << 63:
                # `x > K` / `x >= K` compile to compares against K or K-1.
                feats.update((f"c:{v}", f"c:{v + 1}"))
    syms = subprocess.run(
        [_tool("objdump"), "-T", str(path)], capture_output=True, text=True, check=False
    ).stdout
    for line in syms.splitlines():
        parts = line.split()
        if parts and "*UND*" in line:
            name = parts[-1].split("@")[0]
            if name.startswith("__") and name.endswith("_chk"):
                name = name[2:-4]
            if name in LIBC_SYMBOLS:
                feats.add("i:" + _IMPORT_ALIASES.get(name, name))
    feats |= {"f:" + n for n in _local_function_symbols(path)}
    return FeatureSet(feats, "binary")


def _local_function_symbols(path: Path) -> set[str]:
    out = subprocess.run([_tool("objdump"), "-t", str(path)], capture_output=True, text=True, check=False).stdout
    names = set()
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 6 and " F .text" in line:
            name = parts[-1]
            if not name.startswith(("_", ".")) and name not in ("main", "frame_dummy", "deregister_tm_clones", "register_tm_clones"):
                names.add(name)
    return names
