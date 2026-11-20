"""Difficulty calibration for re_tasks: solve rates per level and baseline.

    python3 -m bench.run_re_tasks_bench --per-cell 40 --out bench/results/re_tasks
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from collections import defaultdict
from pathlib import Path

from re_tasks.generator import ANSWER_FIELDS, generate
from re_tasks.solvers import SOLVERS, solve_file, verify

LEVELS = (0, 1, 2)
OPTS = ("-O0", "-O2", "-Os")


def run(per_cell: int, seed: int, out: Path) -> dict:
    cells: dict = defaultdict(lambda: defaultdict(lambda: {"solved": 0, "score": 0.0, "n": 0, "decoy_c2": 0}))
    hashes, hosts = set(), set()
    n_total = 0
    with tempfile.TemporaryDirectory() as td:
        for level in LEVELS:
            for opt in OPTS:
                for j in range(per_cell):
                    s = seed * 1_000_000 + level * 100_000 + OPTS.index(opt) * 10_000 + j
                    inst = generate(Path(td), level, s, opt)
                    data = Path(inst.binary).read_bytes()
                    hashes.add(hashlib.sha256(data).hexdigest())
                    hosts.add(inst.answer["c2_host"])
                    n_total += 1
                    for name in SOLVERS:
                        sub = solve_file(Path(inst.binary), name)
                        r = verify(sub, inst.answer)
                        c = cells[f"L{level}"][name]
                        c["n"] += 1
                        c["solved"] += r["solved"]
                        c["score"] += r["score"]
                        c["decoy_c2"] += sub.get("c2_host") == inst.decoys["c2_host"]
    table = {
        lvl: {
            name: {
                "n": c["n"],
                "solve_rate": c["solved"] / c["n"],
                "mean_field_score": round(c["score"] / c["n"], 4),
                "fell_for_decoy_c2": c["decoy_c2"] / c["n"],
            }
            for name, c in solvers.items()
        }
        for lvl, solvers in cells.items()
    }
    result = {
        "seed": seed,
        "instances": n_total,
        "levels": list(LEVELS),
        "opts": list(OPTS),
        "fields": list(ANSWER_FIELDS),
        "unique_binaries": len(hashes),
        "unique_c2_hosts": len(hosts),
        "by_level": table,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(result, indent=2))
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-cell", type=int, default=40)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--out", default="bench/results/re_tasks")
    a = ap.parse_args()
    print(json.dumps(run(a.per_cell, a.seed, Path(a.out)), indent=2))


if __name__ == "__main__":
    main()
