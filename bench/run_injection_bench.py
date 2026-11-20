"""Benchmark for re_tasks.injection.detect (AI-analysis-evasion text detector).

Positives: benign RE task binaries carrying evasion text from seven families,
in five encodings, plus Spanish/Russian payloads and four strings quoted in
Cisco Talos' public CAIRN YARA rules. Negatives: the same task binaries with no
text, and real benign files on this machine. No LLM is called; this measures
the static detector only.

    python3 -m bench.run_injection_bench --out bench/results/injection
"""

from __future__ import annotations

import argparse
import json
import tempfile
from collections import defaultdict
from pathlib import Path

from bench.run_llm_indicator_bench import negatives
from re_tasks.injection import ENCODINGS, EXTERNAL_PUBLIC, NON_ENGLISH, PAYLOADS, detect, embed


def run(out_dir: Path, seeds: int, n_neg: int, seed: int) -> dict:
    rows = defaultdict(lambda: [0, 0])
    with tempfile.TemporaryDirectory() as tmp:
        tmpd = Path(tmp)
        clean_fp = 0
        for s in range(seeds):
            clean_fp += detect(embed(tmpd, seed + s, None).read_bytes()).flagged
            groups = [(f"{fam}/{enc}", text, enc) for fam, texts in PAYLOADS.items() for text in texts for enc in ENCODINGS]
            groups += [(f"non_english_{lang}/ascii", t, "ascii") for lang, ts in NON_ENGLISH.items() for t in ts]
            groups += [(f"external_talos/{enc}", t, enc) for t in EXTERNAL_PUBLIC for enc in ("ascii", "utf16")]
            for i, (key, text, enc) in enumerate(groups):
                b = embed(tmpd, seed + s, text, enc, tag=str(i))
                rows[key][0] += detect(b.read_bytes()).flagged
                rows[key][1] += 1
                b.unlink()

    by_family, by_encoding = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
    for key, (k, n) in rows.items():
        fam, enc = key.split("/")
        for agg, name in ((by_family, fam), (by_encoding, enc)):
            agg[name][0] += k
            agg[name][1] += n

    neg_files = negatives(n_neg, seed)
    fp_files = []
    for p in neg_files:
        try:
            d = detect(p.read_bytes())
        except OSError:
            continue
        if d.flagged:
            fp_files.append({"file": str(p), "hits": [{"text": h.text, "categories": h.categories} for h in d.hits[:3]]})

    fmt = lambda agg: {k: {"detected": v[0], "n": v[1], "recall": round(v[0] / v[1], 3)} for k, v in sorted(agg.items())}
    result = {
        "seeds": seeds,
        "by_family": fmt(by_family),
        "by_encoding": fmt(by_encoding),
        "cells": fmt(rows),
        "clean_task_false_positives": {"flagged": clean_fp, "n": seeds},
        "benign_system_files": {"flagged": len(fp_files), "n": len(neg_files), "examples": fp_files[:25]},
        "caveats": [
            "Payloads and detector were written by the same author; recall on own payloads is an upper bound.",
            "External Talos strings were read before the detector was written; not a blind test.",
            "No LLM analyzer was evaluated; flip rates need a model and are not reported here.",
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="bench/results/injection")
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--negatives", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    r = run(Path(a.out), a.seeds, a.negatives, a.seed)
    print(json.dumps({k: r[k] for k in ("by_family", "by_encoding", "clean_task_false_positives")}, indent=1, ensure_ascii=False))
    print("benign system files flagged:", r["benign_system_files"]["flagged"], "/", r["benign_system_files"]["n"])


if __name__ == "__main__":
    main()
