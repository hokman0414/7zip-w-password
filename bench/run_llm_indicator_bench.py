"""Benchmark for provenance.llm_indicators.

Negatives are real benign files already on this machine (system binaries,
shared libraries, Python stdlib). Positives are synthetic, benign programs that
embed key-shaped random strings, LLM endpoints, model names and prompts in the
encodings seen in public reporting, plus obfuscated variants that a static
string scan is expected to miss. No real credential or malware is used.

    python3 -m bench.run_llm_indicator_bench --out bench/results/llm_indicators
"""

from __future__ import annotations

import argparse
import base64
import json
import random
import subprocess
import tempfile
from collections import Counter
from itertools import combinations
from pathlib import Path

from provenance.llm_indicators import IndicatorReport, cluster, scan_file
from tests.test_llm_indicators import fake_anthropic, fake_hf, fake_openai

KEY = b"bench-fingerprint-key-0000000000"
NEG_ROOTS = ["/usr/bin", "/usr/sbin", "/usr/lib/x86_64-linux-gnu", "/usr/lib/python3.12", "/usr/lib/python3"]
MAX_BYTES = 64 * 1024 * 1024

ENDPOINTS = [
    ("https://api.openai.com/v1/chat/completions", "gpt-4o"),
    ("https://api.anthropic.com/v1/messages", "claude-3-5-sonnet-20241022"),
    ("https://router.huggingface.co/v1/chat/completions", "Qwen2.5-Coder-32B-Instruct"),
    ("http://localhost:11434/api/generate", "gpt-oss:20b"),
]
PROMPTS = [
    "You are a Windows systems expert. Output only one-line cmd commands without explanation.",
    "Act as a senior Lua developer and return only the code, do not include markdown.",
    "You are an assistant that will generate a PowerShell one-liner; respond only with code.",
]
MAKERS = [fake_anthropic, fake_openai, fake_hf]


def negatives(limit: int, seed: int) -> list[Path]:
    files = []
    for root in NEG_ROOTS:
        for p in Path(root).rglob("*"):
            try:
                if p.is_file() and not p.is_symlink() and 0 < p.stat().st_size <= MAX_BYTES:
                    files.append(p)
            except OSError:
                continue
    files = sorted(set(files))
    random.Random(seed).shuffle(files)
    return files[:limit]


def _c_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def build_positive(variant: str, secret: str, endpoint: str, model: str, prompt: str, out: Path) -> Path:
    if variant in ("c_ascii", "c_utf16", "c_split", "c_xor"):
        if variant == "c_ascii":
            decl = f'static const char K[] = "{secret}";'
        elif variant == "c_utf16":
            decl = f'static const char16_t K[] = u"{secret}";'
        elif variant == "c_split":
            h = len(secret) // 2
            decl = f'static const char K1[] = "{secret[:h]}"; static const char K2[] = "{secret[h:]}";'
        else:
            enc = ",".join(str(ord(c) ^ 0x5A) for c in secret)
            decl = f"static const unsigned char K[] = {{{enc}}};"
        uses = "K1, K2" if variant == "c_split" else "K"
        src = f"""#include <stdio.h>
#include <uchar.h>
{decl}
static const char E[] = "{_c_escape(endpoint)}";
static const char M[] = "{_c_escape(model)}";
static const char P[] = "{_c_escape(prompt)}";
int main(int argc, char **argv) {{
    const void *v[] = {{{uses}, E, M, P}};
    printf("%p %d\\n", (void *)v[argc % (sizeof v / sizeof v[0])], argc);
    return 0;
}}
"""
        subprocess.run(["gcc", "-O2", "-w", "-o", str(out), "-x", "c", "-"], input=src, text=True, check=True)
        subprocess.run(["strip", "-s", str(out)], check=True)
        return out
    if variant == "py":
        text = f'import requests\nKEY = "{secret}"\nURL = "{endpoint}"\nMODEL = "{model}"\nPROMPT = "{prompt}"\n'
    elif variant == "vbs":
        text = f'Dim k : k = "{secret}"\nurl = "{endpoint}"\nmdl = "{model}"\np = "{prompt}"\n'
    elif variant == "js_b64":
        b = base64.b64encode(secret.encode()).decode()
        text = f'const k = atob("{b}");\nconst u = "{endpoint}";\nconst m = "{model}";\nconst p = "{prompt}";\n'
    else:
        raise ValueError(variant)
    out.write_text(text)
    return out


VARIANTS = ["c_ascii", "c_utf16", "py", "vbs", "c_split", "c_xor", "js_b64"]


def score_negatives(files: list[Path], roots: list[str]) -> dict:
    reports = []
    for p in files:
        try:
            reports.append((p, scan_file(p, KEY)))
        except OSError:
            continue
    tiers = Counter(r.tier for _, r in reports)
    n = max(len(reports), 1)
    examples = {
        tier: sorted(
            repr(
                {
                    "file": str(p),
                    "providers": sorted(r.providers),
                    "models": sorted(r.models)[:5],
                    "credentials": sorted(c.redacted for c in r.credentials),
                    "prompt_prefix": r.prompts[0][:80] if r.prompts else "",
                }
            )
            for p, r in reports
            if r.tier == tier
        )[:10]
        for tier in ("T1", "T2", "T3")
    }
    return {
        "files_scanned": len(reports),
        "roots": roots,
        "tier_counts": dict(tiers),
        "fp_rate_T1": tiers["T1"] / n,
        "fp_rate_T2": tiers["T2"] / n,
        "fp_rate_T3": tiers["T3"] / n,
        "examples": examples,
    }


def run(out_dir: Path, n_neg: int, per_variant: int, n_keys: int, seed: int, llm_sw_root: str | None) -> dict:
    rng = random.Random(seed)
    system_neg = score_negatives(negatives(n_neg, seed), NEG_ROOTS)
    llm_sw_neg = None
    if llm_sw_root:
        files = sorted(p for p in Path(llm_sw_root).rglob("*") if p.is_file() and p.stat().st_size <= MAX_BYTES)
        llm_sw_neg = score_negatives(files, [llm_sw_root])

    keys = [MAKERS[i % len(MAKERS)](seed * 1000 + i) for i in range(n_keys)]
    pos: list[tuple[str, int, IndicatorReport]] = []
    with tempfile.TemporaryDirectory() as td:
        for variant in VARIANTS:
            for j in range(per_variant):
                key_id = rng.randrange(n_keys)
                endpoint, model = rng.choice(ENDPOINTS)
                prompt = rng.choice(PROMPTS) + f" Task id {rng.randrange(10**6)}."
                path = build_positive(variant, keys[key_id], endpoint, model, prompt, Path(td) / f"{variant}_{j}")
                pos.append((variant, key_id, scan_file(path, KEY)))

    per_variant_stats = {}
    for variant in VARIANTS:
        rows = [(k, r) for v, k, r in pos if v == variant]
        per_variant_stats[variant] = {
            "n": len(rows),
            "credential_recall": sum(bool(r.credentials) for _, r in rows) / len(rows),
            "endpoint_recall": sum(bool(r.endpoints) for _, r in rows) / len(rows),
            "model_recall": sum(bool(r.models) for _, r in rows) / len(rows),
            "prompt_recall": sum(bool(r.prompts) for _, r in rows) / len(rows),
            "tier": dict(Counter(r.tier for _, r in rows)),
        }

    found = [(k, r) for _, k, r in pos if r.credentials]
    groups = cluster([r for _, r in found])
    pred = {sha: gi for gi, g in enumerate(groups) for sha in g}
    truth = {r.sha256: k for k, r in found}
    tp = fp = fn = 0
    for a, b in combinations(list(truth), 2):
        same_t, same_p = truth[a] == truth[b], pred[a] == pred[b]
        tp += same_t and same_p
        fp += same_p and not same_t
        fn += same_t and not same_p

    result = {
        "seed": seed,
        "negatives_system": system_neg,
        "negatives_benign_llm_software": llm_sw_neg,
        "positives": per_variant_stats,
        "key_group_clustering": {
            "samples_with_credentials": len(found),
            "distinct_keys": len(set(truth.values())),
            "predicted_groups": len(groups),
            "pairwise_precision": tp / (tp + fp) if tp + fp else None,
            "pairwise_recall": tp / (tp + fn) if tp + fn else None,
        },
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(result, indent=2))
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="bench/results/llm_indicators")
    ap.add_argument("--negatives", type=int, default=5000)
    ap.add_argument("--per-variant", type=int, default=30)
    ap.add_argument("--keys", type=int, default=15)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument(
        "--benign-llm-software",
        help="directory of unpacked benign LLM-integrated packages (e.g. official SDK wheels)",
    )
    a = ap.parse_args()
    r = run(Path(a.out), a.negatives, a.per_variant, a.keys, a.seed, a.benign_llm_software)
    summary = {
        k: ({kk: vv for kk, vv in v.items() if kk != "examples"} if isinstance(v, dict) and "examples" in v else v)
        for k, v in r.items()
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
