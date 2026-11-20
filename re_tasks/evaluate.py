"""Evaluator-side controls for running re_tasks as an independent evaluation.

Three things an outside evaluator must be able to show a lab or regulator:

* Results carry uncertainty: per-level solve rates with Wilson 95% intervals,
  and a two-proportion test before claiming one system beats another.
* The private bank is not in anyone's training data: every task description
  carries a bank-specific canary string, and any text (model output, a data
  dump shared by a lab) can be checked for it.
* No customer is scored on instances another customer has seen: instances are
  assigned to customers by a keyed hash, so partitions are disjoint and stable,
  and every exposure is logged.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from re_tasks.generator import Instance
from re_tasks.solvers import verify

CANARY_PREFIX = "RE-TASKS EVALUATION DATA. MUST NOT APPEAR IN TRAINING CORPORA. canary GUID "


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def two_proportion_p(k1: int, n1: int, k2: int, n2: int) -> float:
    """Two-sided p-value for H0: equal solve rates (pooled z-test)."""
    if n1 == 0 or n2 == 0:
        return 1.0
    pooled = (k1 + k2) / (n1 + n2)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    if se == 0:
        return 1.0
    z = abs(k1 / n1 - k2 / n2) / se
    return math.erfc(z / math.sqrt(2))


@dataclass
class PrivateBank:
    bank_key: bytes
    bank_id: str
    exposures: list[dict] = field(default_factory=list)

    @property
    def canary(self) -> str:
        guid = uuid.UUID(bytes=hmac.new(self.bank_key, self.bank_id.encode(), hashlib.sha256).digest()[:16])
        return CANARY_PREFIX + str(guid)

    def stamp(self, inst: Instance, task_dir: Path) -> None:
        path = Path(task_dir) / f"{inst.task_id}.task.json"
        task = json.loads(path.read_text())
        task["canary"] = self.canary
        path.write_text(json.dumps(task, indent=2))

    def contaminated(self, text: str) -> bool:
        guid = self.canary[len(CANARY_PREFIX):]
        return guid in text or guid.replace("-", "") in text

    def partition(self, task_ids: list[str], customers: list[str]) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {c: [] for c in customers}
        for t in task_ids:
            h = hmac.new(self.bank_key, f"{self.bank_id}|{t}".encode(), hashlib.sha256).digest()
            out[customers[int.from_bytes(h[:4], "big") % len(customers)]].append(t)
        return out

    def evaluate(
        self, customer: str, system: str, solve: Callable[[bytes], dict], instances: list[Instance]
    ) -> dict:
        per_level: dict[int, dict] = defaultdict(lambda: {"n": 0, "solved": 0, "decoy": 0, "score": 0.0})
        for inst in instances:
            self.exposures.append({"customer": customer, "system": system, "task_id": inst.task_id})
            sub = solve(Path(inst.binary).read_bytes())
            r = verify(sub, inst.answer)
            c = per_level[inst.level]
            c["n"] += 1
            c["solved"] += r["solved"]
            c["score"] += r["score"]
            c["decoy"] += sub.get("c2_host") == inst.decoys["c2_host"]
        return {
            "customer": customer,
            "system": system,
            "bank_id": self.bank_id,
            "by_level": {
                f"L{lvl}": {
                    "n": c["n"],
                    "solved": c["solved"],
                    "solve_rate": round(c["solved"] / c["n"], 4),
                    "ci95": [round(x, 4) for x in wilson(c["solved"], c["n"])],
                    "mean_field_score": round(c["score"] / c["n"], 4),
                    "fell_for_decoy_c2": round(c["decoy"] / c["n"], 4),
                }
                for lvl, c in sorted(per_level.items())
            },
        }

    def exposed_to_others(self, customer: str, task_ids: list[str]) -> set[str]:
        return {e["task_id"] for e in self.exposures if e["customer"] != customer} & set(task_ids)


def compare(a: dict, b: dict, level: str) -> dict:
    x, y = a["by_level"][level], b["by_level"][level]
    p = two_proportion_p(x["solved"], x["n"], y["solved"], y["n"])
    return {
        "level": level,
        a["system"]: x["solve_rate"],
        b["system"]: y["solve_rate"],
        "p_value": round(p, 6),
        "claim_allowed": p < 0.05,
    }
