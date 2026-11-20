import json
import shutil
import tempfile
import unittest
from pathlib import Path

from re_tasks.evaluate import PrivateBank, compare, two_proportion_p, wilson
from re_tasks.generator import generate
from re_tasks.solvers import SOLVERS


class EvaluateStatsTests(unittest.TestCase):
    def test_wilson_bounds(self):
        lo, hi = wilson(0, 40)
        self.assertEqual(lo, 0.0)
        self.assertGreater(hi, 0.05)
        lo, hi = wilson(40, 40)
        self.assertLess(lo, 0.95)
        self.assertEqual(hi, 1.0)
        lo, hi = wilson(20, 40)
        self.assertTrue(lo < 0.5 < hi)

    def test_two_proportion(self):
        self.assertGreater(two_proportion_p(20, 40, 21, 40), 0.5)
        self.assertLess(two_proportion_p(5, 40, 35, 40), 1e-6)


class PrivateBankTests(unittest.TestCase):
    def setUp(self):
        self.bank = PrivateBank(bank_key=b"k" * 32, bank_id="bank-2026-q4")

    def test_canary_is_bank_specific_and_detectable(self):
        other = PrivateBank(bank_key=b"k" * 32, bank_id="bank-2027-q1")
        self.assertNotEqual(self.bank.canary, other.canary)
        self.assertTrue(self.bank.contaminated("... model said: " + self.bank.canary + " ..."))
        self.assertFalse(self.bank.contaminated("... " + other.canary))
        guid = self.bank.canary.split()[-1]
        self.assertTrue(self.bank.contaminated(guid.replace("-", "").upper().lower()))

    def test_partitions_are_disjoint_complete_and_stable(self):
        ids = [f"re-L2-{i:08x}" for i in range(300)]
        p1 = self.bank.partition(ids, ["lab-a", "lab-b", "lab-c"])
        p2 = self.bank.partition(ids, ["lab-a", "lab-b", "lab-c"])
        self.assertEqual(p1, p2)
        self.assertEqual(sorted(sum(p1.values(), [])), sorted(ids))
        self.assertTrue(all(len(v) > 60 for v in p1.values()))

    @unittest.skipUnless(shutil.which("gcc") and shutil.which("strip"), "needs gcc")
    def test_evaluate_stamps_logs_and_compares(self):
        with tempfile.TemporaryDirectory() as td:
            insts = [generate(Path(td), 2, s) for s in range(6)]
            for inst in insts:
                self.bank.stamp(inst, Path(td))
            task = json.loads((Path(td) / f"{insts[0].task_id}.task.json").read_text())
            self.assertEqual(task["canary"], self.bank.canary)
            a = self.bank.evaluate("lab-a", "family_extractor", SOLVERS["family_extractor"], insts)
            b = self.bank.evaluate("lab-a", "strings", SOLVERS["strings"], insts)
            self.assertEqual(a["by_level"]["L2"]["solved"], 6)
            self.assertEqual(b["by_level"]["L2"]["solved"], 0)
            self.assertTrue(compare(a, b, "L2")["claim_allowed"])
            self.assertEqual(self.bank.exposed_to_others("lab-b", [i.task_id for i in insts]),
                             {i.task_id for i in insts})


if __name__ == "__main__":
    unittest.main()
