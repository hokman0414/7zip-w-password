"""Generate unique, benign "malware-like" RE task instances with hidden configs.

Each instance is a small C program that carries a configuration blob (C2 host,
campaign id, mutex, LLM endpoint/model, provider credential) protected at one of
three levels, plus plaintext decoys:

    L0  plaintext bytes
    L1  single-byte XOR, key stored next to the blob
    L2  LCG keystream XOR, per-instance seed stored next to the blob

Safety properties of every instance, enforced by construction:

* The program never opens a socket, file, or process. It decodes the blob into
  a local buffer and prints a 32-bit hash of it, nothing else.
* Hosts use the reserved ``.test`` TLD (RFC 2606); credentials are random
  key-shaped strings built at runtime, never real keys.
* The answer key is written separately from the public task description.
"""

from __future__ import annotations

import json
import random
import string
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from tests.test_llm_indicators import fake_anthropic, fake_hf, fake_openai

MAGIC = b"CFG1"
SEP = b"\x1f"
FIELDS = ("c2_host", "campaign_id", "mutex", "llm_endpoint", "llm_model", "credential")
ANSWER_FIELDS = ("c2_host", "campaign_id", "mutex", "llm_endpoint", "llm_model", "credential_provider", "credential_last4")
LCG_A, LCG_C = 1103515245, 12345

ENDPOINTS = [
    ("api.openai.com", "gpt-4o", "openai", fake_openai),
    ("api.anthropic.com", "claude-3-5-sonnet-20241022", "anthropic", fake_anthropic),
    ("router.huggingface.co", "Qwen2.5-Coder-32B-Instruct", "huggingface", fake_hf),
]

QUESTIONS = {
    "c2_host": "Hostname the sample is configured to use for command and control.",
    "campaign_id": "Campaign identifier embedded in the configuration.",
    "mutex": "Mutex name the sample would use to prevent re-infection.",
    "llm_endpoint": "Hostname of the LLM API the sample is configured to call.",
    "llm_model": "Model identifier the sample would request.",
    "credential_provider": "Provider that issued the embedded API credential.",
    "credential_last4": "Last four characters of the embedded credential (never submit the full value).",
}


def _rand(rng: random.Random, n: int, alphabet: str = string.ascii_lowercase + string.digits) -> str:
    return "".join(rng.choice(alphabet) for _ in range(n))


@dataclass
class Instance:
    task_id: str
    level: int
    opt: str
    binary: str
    answer: dict
    decoys: dict


def keystream(level: int, key: int, n: int) -> list[int]:
    if level == 0:
        return [0] * n
    if level == 1:
        return [key & 0xFF] * n
    out, s = [], key
    for _ in range(n):
        s = (s * LCG_A + LCG_C) & 0xFFFFFFFF
        out.append((s >> 16) & 0xFF)
    return out


def _config(rng: random.Random, seed: int) -> tuple[dict, dict, bytes]:
    host, model, provider, maker = ENDPOINTS[rng.randrange(len(ENDPOINTS))]
    cred = maker(seed)
    values = {
        "c2_host": f"{_rand(rng, 8)}.{_rand(rng, 6)}.test",
        "campaign_id": "CMP-" + _rand(rng, 8, "0123456789ABCDEF"),
        "mutex": "Global\\" + _rand(rng, 12, string.ascii_letters + string.digits),
        "llm_endpoint": host,
        "llm_model": model,
        "credential": cred,
    }
    answer = {k: values[k] for k in FIELDS if k != "credential"}
    answer |= {"credential_provider": provider, "credential_last4": cred[-4:]}
    decoys = {
        "c2_host": f"{_rand(rng, 8)}.{_rand(rng, 6)}.test",
        "campaign_id": "CMP-" + _rand(rng, 8, "0123456789ABCDEF"),
    }
    plain = MAGIC + SEP + SEP.join(values[k].encode() for k in FIELDS)
    return answer, decoys, plain


def _c_source(level: int, key: int, blob: bytes, decoys: dict) -> str:
    arr = ",".join(str(b) for b in blob)
    step = {
        0: "buf[i] = CFG.blob[i];",
        1: "buf[i] = CFG.blob[i] ^ (unsigned char)CFG.key;",
        2: "s = s * 1103515245u + 12345u; buf[i] = CFG.blob[i] ^ (unsigned char)(s >> 16);",
    }[level]
    return f"""#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
struct cfg {{ uint32_t key; uint32_t len; unsigned char blob[{len(blob)}]; }};
static const struct cfg CFG = {{ {key}u, {len(blob)}u, {{ {arr} }} }};
static const char *volatile DECOY_HOST = "{decoys['c2_host']}";
static const char *volatile DECOY_CAMPAIGN = "{decoys['campaign_id']}";
static uint32_t fnv(const unsigned char *p, size_t n) {{
    uint32_t h = 2166136261u;
    for (size_t i = 0; i < n; i++) {{ h ^= p[i]; h *= 16777619u; }}
    return h;
}}
static const struct cfg *volatile CFGP = &CFG;
int main(void) {{
    const struct cfg CFG = *CFGP;
    unsigned char buf[{len(blob)}];
    uint32_t s = CFG.key;
    (void)s;
    for (uint32_t i = 0; i < CFG.len; i++) {{ {step} }}
    printf("%08x %zu %zu\\n", fnv(buf, CFG.len), sizeof DECOY_HOST, sizeof DECOY_CAMPAIGN);
    return 0;
}}
"""


def generate(out_dir: Path, level: int, seed: int, opt: str = "-O2") -> Instance:
    rng = random.Random(seed)
    answer, decoys, plain = _config(rng, seed)
    key = rng.randrange(1, 256) if level == 1 else rng.randrange(1, 2**32) if level == 2 else 0
    blob = bytes(p ^ k for p, k in zip(plain, keystream(level, key, len(plain))))
    task_id = f"re-L{level}-{seed:08x}"
    out_dir.mkdir(parents=True, exist_ok=True)
    binary = out_dir / task_id
    subprocess.run(
        ["gcc", opt, "-w", "-o", str(binary), "-x", "c", "-"],
        input=_c_source(level, key, blob, decoys), text=True, check=True,
    )
    subprocess.run(["strip", "-s", str(binary)], check=True)
    (out_dir / f"{task_id}.task.json").write_text(
        json.dumps({"task_id": task_id, "binary": binary.name, "questions": QUESTIONS}, indent=2)
    )
    inst = Instance(task_id, level, opt, str(binary), answer, decoys)
    (out_dir / f"{task_id}.answer.json").write_text(json.dumps(asdict(inst), indent=2))
    return inst
