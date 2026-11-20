"""Demo of an independent-evaluator report on a private re_tasks bank.

The "systems under test" are the three baseline solvers, not AI models: no
model was run and nothing was sent to an external service. The point is to
measure the evaluator controls (partitioning, canaries, uncertainty) and to
show what can honestly be claimed at a given sample size.

    python3 -m bench.run_re_eval_report --per-level 60
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from re_tasks.evaluate import PrivateBank, compare
from re_tasks.generator import generate
from re_tasks.solvers import SOLVERS

CUSTOMERS = ["lab-a", "lab-b", "lab-c"]


def run(per_level: int, seed: int) -> dict:
    bank = PrivateBank(bank_key=seed.to_bytes(4, "big") * 8, bank_id=f"demo-bank-{seed}")
    with tempfile.TemporaryDirectory() as td:
        insts = [generate(Path(td), lvl, seed * 100_000 + lvl * 10_000 + j) for lvl in (0, 1, 2) for j in range(per_level)]
        for inst in insts:
            bank.stamp(inst, Path(td))
        stamped = sum(json.loads((Path(td) / f"{i.task_id}.task.json").read_text()).get("canary") == bank.canary for i in insts)
        by_id = {i.task_id: i for i in insts}
        parts = bank.partition(list(by_id), CUSTOMERS)
        reports, comparisons, overlap = {}, [], {}
        for cust, ids in parts.items():
            overlap[cust] = len(bank.exposed_to_others(cust, ids))
            subset = [by_id[t] for t in ids]
            reports[cust] = {name: bank.evaluate(cust, name, fn, subset) for name, fn in SOLVERS.items()}
            for lvl in ("L0", "L1", "L2"):
                comparisons.append({"customer": cust} | compare(reports[cust]["family_extractor"], reports[cust]["xor_bruteforce"], lvl))
        leaked_canary = sum(
            bank.contaminated(json.dumps(fn(Path(i.binary).read_bytes()))) for i in insts for fn in SOLVERS.values()
        )
    return {
        "note": "systems under test are baseline solvers, not AI models",
        "instances": len(insts),
        "canary_stamped": stamped,
        "canary_found_in_solver_outputs": leaked_canary,
        "partition_sizes": {c: len(v) for c, v in parts.items()},
        "cross_customer_overlap_before_scoring": overlap,
        "reports": reports,
        "family_extractor_vs_xor_bruteforce": comparisons,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-level", type=int, default=60)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="bench/results/re_eval_report/results.json")
    a = ap.parse_args()
    res = run(a.per_level, a.seed)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "reports"}, indent=2))


if __name__ == "__main__":
    main()
