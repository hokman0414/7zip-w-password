import json
import shutil
import tempfile
import unittest
from pathlib import Path

from re_tasks.generator import ANSWER_FIELDS, generate
from re_tasks.solvers import solve_file, verify

HAVE_GCC = shutil.which("gcc") is not None and shutil.which("strip") is not None


@unittest.skipUnless(HAVE_GCC, "gcc/strip required")
class RETaskTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_family_extractor_solves_every_level(self):
        for level in (0, 1, 2):
            inst = generate(self.dir, level, seed=100 + level)
            result = verify(solve_file(Path(inst.binary), "family_extractor"), inst.answer)
            self.assertTrue(result["solved"], (level, result))

    def test_difficulty_gradient(self):
        l1 = generate(self.dir, 1, seed=201)
        l2 = generate(self.dir, 2, seed=202)
        self.assertTrue(verify(solve_file(Path(l1.binary), "xor_bruteforce"), l1.answer)["solved"])
        self.assertFalse(verify(solve_file(Path(l2.binary), "xor_bruteforce"), l2.answer)["solved"])
        s2 = verify(solve_file(Path(l2.binary), "strings"), l2.answer)
        self.assertFalse(s2["fields"]["c2_host"])
        self.assertFalse(s2["fields"]["credential_last4"])

    def test_public_task_and_answer_hide_full_credential(self):
        inst = generate(self.dir, 2, seed=301)
        task = (self.dir / f"{inst.task_id}.task.json").read_text()
        self.assertNotIn(inst.answer["c2_host"], task)
        answer = json.loads((self.dir / f"{inst.task_id}.answer.json").read_text())
        self.assertEqual(len(answer["answer"]["credential_last4"]), 4)
        self.assertEqual(set(answer["answer"]), set(ANSWER_FIELDS))

    def test_instances_are_unique(self):
        a = generate(self.dir, 2, seed=401)
        b = generate(self.dir, 2, seed=402)
        self.assertNotEqual(Path(a.binary).read_bytes(), Path(b.binary).read_bytes())
        self.assertNotEqual(a.answer["c2_host"], b.answer["c2_host"])

    def test_verifier_partial_credit(self):
        answer = {"c2_host": "a", "campaign_id": "b", "mutex": "c", "llm_endpoint": "d",
                  "llm_model": "e", "credential_provider": "f", "credential_last4": "g"}
        sub = dict(answer, c2_host="wrong")
        r = verify(sub, answer)
        self.assertFalse(r["solved"])
        self.assertAlmostEqual(r["score"], 6 / 7)


if __name__ == "__main__":
    unittest.main()
