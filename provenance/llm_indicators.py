"""Static indicators of LLM-enabled malware (Cycle 4 wedge prototype).

Finds the artifacts that public research uses to hunt malware which calls an
LLM at runtime (SentinelOne LABScon 2025; Google GTIG AI Threat Tracker 2025):

    credential  provider API key embedded in the sample
    endpoint    hosted-LLM API hostname or local inference endpoint
    model       model identifier string (e.g. "gpt-4", "Qwen2.5-Coder")
    prompt      natural-language instruction string ("prompts as code")

Handling rules enforced here, not left to callers:

* A credential is never returned or stored in full. Reports keep the provider,
  a redacted form (prefix + last 4) and a keyed fingerprint for clustering.
  The issuing provider can re-extract the full key itself from the sample hash
  and byte offset, so the full secret never has to leave the sample.
* Nothing in this module validates, calls, or otherwise uses a credential.
* Key formats are public heuristics; only the issuing provider can confirm a
  match is a real key and map it to an account.
"""

from __future__ import annotations

import hashlib
import hmac
import re
from dataclasses import dataclass, field
from pathlib import Path

# Anthropic "sk-ant-api03-" and OpenAI's base64("OpenAI") marker are the
# patterns SentinelOne reported hunting with; HF "hf_" and Google "AIza" are the
# providers' published token prefixes.
CREDENTIAL_PATTERNS: dict[str, re.Pattern[bytes]] = {
    "anthropic": re.compile(rb"sk-ant-(?:api|admin)\d{2}-[A-Za-z0-9_\-]{20,}"),
    "openai": re.compile(rb"sk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_\-]{8,}T3BlbkFJ[A-Za-z0-9_\-]{8,}"),
    "huggingface": re.compile(rb"(?<![A-Za-z0-9])hf_[A-Za-z0-9]{30,40}(?![A-Za-z0-9])"),
    "google": re.compile(rb"AIza[0-9A-Za-z_\-]{35}"),
}

ENDPOINTS: dict[bytes, str] = {
    b"api.openai.com": "openai",
    b"api.anthropic.com": "anthropic",
    b"generativelanguage.googleapis.com": "google",
    b"api-inference.huggingface.co": "huggingface",
    b"router.huggingface.co": "huggingface",
    b"api.mistral.ai": "mistral",
    b"api.x.ai": "xai",
    b"api.deepseek.com": "deepseek",
    b"openrouter.ai/api": "openrouter",
    b"api.together.xyz": "together",
    b"api.groq.com": "groq",
    b"localhost:11434": "ollama-local",
    b"127.0.0.1:11434": "ollama-local",
}

MODEL_RE = re.compile(
    rb"(?<![A-Za-z0-9])("
    rb"gpt-(?:3\.5|4o?|4\.1|5|oss)[A-Za-z0-9.:_\-]*"
    rb"|claude-[0-9a-z][A-Za-z0-9.\-]*"
    rb"|gemini-[0-9][A-Za-z0-9.\-]*"
    rb"|qwen[0-9][A-Za-z0-9.\-]*"
    rb"|deepseek-(?:coder|chat|r1|v[0-9])[A-Za-z0-9.\-]*"
    rb"|mistral-(?:large|small|medium|7b)[A-Za-z0-9.\-]*"
    rb"|llama-?[0-9][A-Za-z0-9.\-]*"
    rb")",
    re.I,
)

PROMPT_MARKERS = (
    "you are a", "you are an", "act as", "respond only", "respond with",
    "output only", "only output", "return only", "do not include",
    "without explanation", "no explanation", "generate a", "write a",
    "one-line", "one line", "as an expert", "system prompt",
)
MIN_PROMPT_LEN = 40
MIN_STRING_LEN = 6

_ASCII_RE = re.compile(rb"[\x20-\x7e]{%d,}" % MIN_STRING_LEN)
_UTF16_RE = re.compile(rb"(?:[\x20-\x7e]\x00){%d,}" % MIN_STRING_LEN)


@dataclass(frozen=True)
class CredentialHit:
    provider: str
    redacted: str
    fingerprint: str
    offset: int
    encoding: str


@dataclass
class IndicatorReport:
    sha256: str
    credentials: list[CredentialHit] = field(default_factory=list)
    endpoints: dict[str, set[str]] = field(default_factory=dict)
    models: set[str] = field(default_factory=set)
    prompts: list[str] = field(default_factory=list)

    @property
    def providers(self) -> set[str]:
        return {c.provider for c in self.credentials} | set(self.endpoints)

    @property
    def tier(self) -> str:
        """Evidence tier for triage; never a maliciousness verdict.

        T1  embedded credential: provider-verifiable link to an account
        T2  endpoint plus model or prompt: calls a specific LLM service
        T3  model/prompt strings only: weak lead
        """
        if self.credentials:
            return "T1"
        if self.endpoints and (self.models or self.prompts):
            return "T2"
        if self.endpoints or self.models or self.prompts:
            return "T3"
        return "none"


def _redact(secret: str) -> str:
    head = secret[:7] if secret.startswith(("sk-ant", "sk-proj", "sk-svca", "sk-admi")) else secret[:4]
    return f"{head}...{secret[-4:]}"


def _fingerprint(key: bytes, secret: bytes) -> str:
    return hmac.new(key, secret, hashlib.sha256).hexdigest()[:24]


def _strings(data: bytes) -> list[tuple[int, str, str]]:
    out = [(m.start(), m.group().decode("ascii"), "ascii") for m in _ASCII_RE.finditer(data)]
    out += [(m.start(), m.group().decode("utf-16-le"), "utf16le") for m in _UTF16_RE.finditer(data)]
    return out


def _looks_like_prompt(s: str) -> bool:
    if len(s) < MIN_PROMPT_LEN or s.count(" ") < 6:
        return False
    low = s.lower()
    return sum(marker in low for marker in PROMPT_MARKERS) >= 2


def scan_bytes(data: bytes, fingerprint_key: bytes) -> IndicatorReport:
    report = IndicatorReport(sha256=hashlib.sha256(data).hexdigest())
    seen: set[str] = set()
    for offset, s, encoding in _strings(data):
        raw = s.encode("ascii", "ignore")
        for provider, pattern in CREDENTIAL_PATTERNS.items():
            for m in pattern.finditer(raw):
                secret = m.group()
                fp = _fingerprint(fingerprint_key, secret)
                if fp in seen:
                    continue
                seen.add(fp)
                step = 2 if encoding == "utf16le" else 1
                report.credentials.append(
                    CredentialHit(provider, _redact(secret.decode()), fp, offset + m.start() * step, encoding)
                )
        low = raw.lower()
        for host, provider in ENDPOINTS.items():
            if host in low:
                report.endpoints.setdefault(provider, set()).add(host.decode())
        for m in MODEL_RE.finditer(raw):
            report.models.add(m.group().decode().lower())
        if _looks_like_prompt(s):
            report.prompts.append(s[:200])
    return report


def scan_file(path: Path, fingerprint_key: bytes) -> IndicatorReport:
    return scan_bytes(Path(path).read_bytes(), fingerprint_key)


def cluster(reports: list[IndicatorReport]) -> list[list[str]]:
    """Group samples that share a credential fingerprint or an exact prompt.

    Shared keys link samples to one provider account (SentinelOne's key-group
    method). A shared key is evidence of shared infrastructure or a shared leak,
    not proof of a shared author.
    """
    parent = {r.sha256: r.sha256 for r in reports}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    owner: dict[str, str] = {}
    for r in reports:
        links = [c.fingerprint for c in r.credentials]
        links += ["p:" + hashlib.sha256(p.encode()).hexdigest() for p in r.prompts]
        for link in links:
            if link in owner:
                parent[find(r.sha256)] = find(owner[link])
            else:
                owner[link] = r.sha256
    groups: dict[str, list[str]] = {}
    for r in reports:
        groups.setdefault(find(r.sha256), []).append(r.sha256)
    return sorted((sorted(g) for g in groups.values()), key=lambda g: (-len(g), g[0]))


def disclosure_packets(reports: list[IndicatorReport]) -> dict[str, list[dict]]:
    """Per-provider packets for responsible disclosure of embedded credentials.

    Each entry gives the provider what it needs to re-extract the key from the
    sample itself (sha256 + offset + encoding) without the full secret being
    copied anywhere else.
    """
    packets: dict[str, list[dict]] = {}
    for r in reports:
        for c in r.credentials:
            packets.setdefault(c.provider, []).append(
                {
                    "sample_sha256": r.sha256,
                    "offset": c.offset,
                    "encoding": c.encoding,
                    "redacted": c.redacted,
                    "fingerprint": c.fingerprint,
                    "note": "Format match only; not validated or used.",
                }
            )
    return packets
