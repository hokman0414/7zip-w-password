"""Synthetic benign C program generator for the provenance benchmark.

Programs are rendered from a structured spec so controlled transforms can be
applied (constant mutation, string obfuscation, identifier renaming, function
reordering, partial reuse inside another host). Nothing here is malicious and
nothing here is real AI-generated code; it is a stand-in corpus whose feature
distinctiveness is deliberately tunable.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field, replace

VERBS = "load parse open validate compute flush encode decode allocate resolve sync update read write scan".split()
NOUNS = (
    "config buffer header record session packet entry token cache index table frame block segment "
    "checksum payload manifest queue cursor bucket channel ledger profile snapshot"
).split()
QUALS = "file stream request response value list map node field limit window offset".split()
OUTCOMES = ["failed", "succeeded", "is invalid", "exceeds limit", "not found", "completed", "timed out", "was skipped"]

COMMON_STRINGS = [
    "Error: memory allocation failed",
    "Usage: program [options] <input>",
    "Invalid argument provided",
    "Operation completed successfully",
    "Failed to open input file",
    "Processing complete",
    "Unexpected end of input",
    "Buffer overflow detected",
    "Initializing subsystem",
    "Shutting down gracefully",
    "Configuration loaded",
    "Warning: value out of range",
]
COMMON_CONSTANTS = [1024, 4096, 65536, 1000, 3600, 86400, 0xEDB88320, 65599, 0x5A5A, 2048, 8192, 0x1F, 9973, 31337]

# Probability that a string/constant is drawn from the shared boilerplate pool
# rather than being program-specific. Higher values make retrieval harder.
COMMON_FRAC = 0.35


def _message(rng: random.Random) -> str:
    if rng.random() < COMMON_FRAC:
        return rng.choice(COMMON_STRINGS)
    return f"{rng.choice(VERBS).capitalize()} {rng.choice(NOUNS)} {rng.choice(QUALS)} {rng.choice(OUTCOMES)}"


def _constant(rng: random.Random) -> int:
    if rng.random() < COMMON_FRAC:
        return rng.choice(COMMON_CONSTANTS)
    return rng.randint(300, 1 << 20)


# Each template: (body, n_constants, n_strings). Placeholders: {fn} {K0..} {S0..}.
TEMPLATES = [
    (
        """unsigned {fn}(const unsigned char *d, unsigned n) {{
    unsigned h = {K0}u;
    for (unsigned i = 0; i < n; i++) h = (h ^ d[i]) * {K1}u;
    if (h % {K2}u == 0) puts("{S0}");
    return h;
}}""",
        3, 1,
    ),
    (
        """int {fn}(int v) {{
    if (v > {K0}) {{ printf("{S0}: %d\\n", v); return -1; }}
    if (v < -{K1}) {{ puts("{S1}"); return -2; }}
    return v * 3 + {K2};
}}""",
        3, 2,
    ),
    (
        """long {fn}(int n) {{
    long acc = 0;
    for (int i = 0; i < n; i++) acc += (i * {K0}L) % {K1}L;
    if (acc > {K2}L) fprintf(stderr, "{S0}\\n");
    return acc;
}}""",
        3, 1,
    ),
    (
        """int {fn}(const char *s) {{
    if (!s || !*s) {{ puts("{S0}"); return 0; }}
    size_t n = strlen(s);
    if (n > {K0}) {{ printf("{S1} (%zu)\\n", n); return -1; }}
    return (int)(n * {K1} % {K2});
}}""",
        3, 2,
    ),
    (
        """unsigned {fn}(unsigned x) {{
    unsigned crc = {K0}u;
    for (int b = 0; b < 32; b++) crc = (crc >> 1) ^ (({K1}u) & (0u - ((crc ^ (x >> b)) & 1u)));
    if (crc == {K2}u) puts("{S0}");
    return crc;
}}""",
        3, 1,
    ),
    (
        """int {fn}(int *arr, int n) {{
    int seen = 0;
    for (int i = 0; i < n; i++) if (arr[i] == {K0} || arr[i] == {K1}) seen++;
    if (seen == 0) printf("{S0}\\n");
    else printf("{S1}: %d\\n", seen);
    return seen;
}}""",
        2, 2,
    ),
    (
        """double {fn}(double t) {{
    double r = t * {K0}.0 / {K1}.0;
    if (r > {K2}.0) {{ puts("{S0}"); r = {K2}.0; }}
    return r;
}}""",
        3, 1,
    ),
    (
        """int {fn}(int state, int ev) {{
    switch (state) {{
    case 0: return ev == {K0} ? 1 : 0;
    case 1: if (ev == {K1}) {{ puts("{S0}"); return 2; }} return 1;
    case 2: return ev == {K2} ? 0 : 2;
    default: puts("{S1}"); return -1;
    }}
}}""",
        3, 2,
    ),
    (
        """void *{fn}(size_t n) {{
    if (n == 0 || n > {K0}) {{ fprintf(stderr, "{S0}\\n"); return NULL; }}
    void *p = calloc(n, {K1} % 64 + 1);
    if (!p) puts("{S1}");
    return p;
}}""",
        2, 2,
    ),
    (
        """int {fn}(const char *key, int dflt) {{
    const char *v = getenv(key);
    if (!v) {{ printf("{S0}: %s\\n", key); return dflt; }}
    long x = strtol(v, NULL, 10);
    if (x < {K0} || x > {K1}) {{ puts("{S1}"); return dflt; }}
    return (int)x;
}}""",
        2, 2,
    ),
    (
        """unsigned long {fn}(unsigned long seed) {{
    seed ^= seed << 13; seed ^= seed >> 7; seed ^= seed << 17;
    seed = seed * {K0}UL + {K1}UL;
    if ((seed & 0xFFFF) == {K2}UL) puts("{S0}");
    return seed;
}}""",
        3, 1,
    ),
    (
        """int {fn}(const char *line) {{
    char buf[{K0}];
    snprintf(buf, sizeof buf, "{S0} %s", line ? line : "");
    if (strstr(buf, "{S1}")) return {K1};
    return (int)strlen(buf);
}}""",
        2, 2,
    ),
]


@dataclass
class FuncSpec:
    template: int
    name: str
    consts: list[int]
    strings: list[str]


@dataclass
class ProgramSpec:
    pid: str
    funcs: list[FuncSpec] = field(default_factory=list)


def _ident(rng: random.Random) -> str:
    return f"{rng.choice(VERBS)}_{rng.choice(NOUNS)}_{rng.choice(QUALS)}_{rng.randint(0, 99)}"


def random_func(rng: random.Random) -> FuncSpec:
    t = rng.randrange(len(TEMPLATES))
    _, nk, ns = TEMPLATES[t]
    return FuncSpec(t, _ident(rng), [_constant(rng) for _ in range(nk)], [_message(rng) for _ in range(ns)])


def random_program(pid: str, rng: random.Random, n_min: int = 3, n_max: int = 6) -> ProgramSpec:
    return ProgramSpec(pid, [random_func(rng) for _ in range(rng.randint(n_min, n_max))])


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _obfuscated(s: str, key: int) -> str:
    data = ",".join(str(b ^ key) for b in s.encode())
    return f"__deobf((const unsigned char[]){{{data}}}, {len(s)}, {key})"


DEOBF = """static const char *__deobf(const unsigned char *d, int n, int k) {
    static char slots[8][128]; static int slot = 0;
    char *o = slots[slot++ & 7];
    for (int i = 0; i < n && i < 127; i++) o[i] = (char)(d[i] ^ k);
    o[n < 127 ? n : 127] = 0;
    return o;
}
"""


def _render_func(f: FuncSpec, obfuscate: bool, key: int) -> str:
    body, _, _ = TEMPLATES[f.template]
    vals = {"fn": f.name}
    for i, k in enumerate(f.consts):
        vals[f"K{i}"] = str(k)
    for i in range(len(f.strings)):
        vals[f"S{i}"] = "{S%d}" % i
    text = body.format(**vals)
    for i, s in enumerate(f.strings):
        token = "{S%d}" % i
        if obfuscate:
            text = re.sub(r'"([^"]*)\{S%d\}([^"]*)"' % i, lambda m: _obfuscated(m.group(1) + s + m.group(2).replace("\\n", "\n"), key), text)
        else:
            text = text.replace(token, _escape(s))
    return text


_CALLS = {
    0: '{fn}((const unsigned char *)"seed-data", 9)',
    1: "{fn}(argc * 7)",
    2: "{fn}(argc + 10)",
    3: '{fn}(argv[0])',
    4: "{fn}((unsigned)argc)",
    5: "{fn}(arr, 4)",
    6: "{fn}((double)argc)",
    7: "{fn}(argc % 3, argc)",
    8: "{fn}((size_t)argc * 4)",
    9: '{fn}("PROV_BENCH_VALUE", argc)',
    10: "{fn}((unsigned long)argc)",
    11: "{fn}(argv[0])",
}


def render(spec: ProgramSpec, obfuscate_strings: bool = False, order: list[int] | None = None) -> str:
    key = (sum(map(ord, spec.pid)) % 200) + 17
    order = order or list(range(len(spec.funcs)))
    parts = ["#include <stdio.h>", "#include <stdlib.h>", "#include <string.h>", ""]
    if obfuscate_strings:
        parts.append(DEOBF)
    for i in order:
        parts.append(_render_func(spec.funcs[i], obfuscate_strings, key))
        parts.append("")
    parts.append("int main(int argc, char **argv) {")
    parts.append("    int arr[4] = {argc, argc + 1, argc * 2, 7};")
    parts.append("    long sink = 0; (void)arr;")
    for f in spec.funcs:
        call = _CALLS[f.template].format(fn=f.name)
        if f.template == 8:
            parts.append(f"    {{ void *p = {call}; sink += p != NULL; free(p); }}")
        else:
            parts.append(f"    sink += (long){call};")
    parts.append('    printf("%ld\\n", sink);')
    parts.append("    return 0;")
    parts.append("}")
    return "\n".join(parts) + "\n"


def mutate_constants(spec: ProgramSpec, rng: random.Random, frac: float = 0.5) -> ProgramSpec:
    funcs = []
    for f in spec.funcs:
        consts = [rng.randint(300, 1 << 20) if rng.random() < frac else k for k in f.consts]
        funcs.append(replace(f, consts=consts))
    return ProgramSpec(spec.pid, funcs)


def refactor(spec: ProgramSpec, rng: random.Random) -> tuple[ProgramSpec, list[int]]:
    """Rename every function and shuffle definition order (semantics unchanged)."""
    funcs = [replace(f, name=f"fn_{rng.getrandbits(32):08x}") for f in spec.funcs]
    order = list(range(len(funcs)))
    rng.shuffle(order)
    return ProgramSpec(spec.pid, funcs), order


def iterate(spec: ProgramSpec, rng: random.Random, new_pid: str) -> ProgramSpec:
    """Simulate a follow-up turn in the same session: tweak one message, maybe add a function."""
    funcs = [replace(f, strings=list(f.strings), consts=list(f.consts)) for f in spec.funcs]
    victim = rng.choice(funcs)
    if victim.strings:
        victim.strings[rng.randrange(len(victim.strings))] = _message(rng)
    if rng.random() < 0.5:
        funcs.append(random_func(rng))
    return ProgramSpec(new_pid, funcs)


def transplant(donor: ProgramSpec, rng: random.Random, new_pid: str, n_take: int = 2, n_host: int = 3) -> ProgramSpec:
    """Embed part of a donor (e.g. proprietary module) inside an unrelated host program."""
    take = rng.sample(donor.funcs, min(n_take, len(donor.funcs)))
    host = [random_func(rng) for _ in range(n_host)]
    funcs = host + [replace(f, name=f"vendor_{f.name}") for f in take]
    rng.shuffle(funcs)
    return ProgramSpec(new_pid, funcs)
