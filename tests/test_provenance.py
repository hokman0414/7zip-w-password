import random
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from bench import synth
from provenance.features import extract_binary, extract_source, normalize_string
from provenance.index import FingerprintIndex, decide
from provenance.service import AccessDenied, AuditLog, InvestigationService, Principal, Thresholds

HAVE_GCC = shutil.which("gcc") is not None and shutil.which("objdump") is not None
KEY = b"0123456789abcdef0123456789abcdef"


def _compile(src: str, out: Path, flags=("-O2",), strip=False) -> Path:
    subprocess.run(["gcc", *flags, "-w", "-o", str(out), "-x", "c", "-"], input=src, text=True, check=True)
    if strip:
        subprocess.run(["strip", "-s", str(out)], check=True)
    return out


class FeatureTests(unittest.TestCase):
    def test_normalize_string_drops_format_and_newline(self):
        self.assertEqual(normalize_string("Read failed: %d\\n"), "read failed:")
        self.assertIsNone(normalize_string("%d %s"))

    def test_source_features_typed(self):
        code = 'int f(int x){ if (x > 70000) puts("Cache bucket overflow detected"); return x; }'
        fs = extract_source(code, include_winnow=False)
        self.assertIn("c:70000", fs.features)
        self.assertIn("s:cache bucket overflow detected", fs.features)
        self.assertIn("i:printf", fs.features)  # puts is canonicalized
        self.assertIn("f:f", fs.features)

    @unittest.skipUnless(HAVE_GCC, "gcc/objdump required")
    def test_binary_recovers_source_features_after_strip(self):
        spec = synth.random_program("x", random.Random(3))
        src = synth.render(spec)
        with tempfile.TemporaryDirectory() as d:
            b = extract_binary(_compile(src, Path(d) / "a", ("-O3",), strip=True))
        s = extract_source(src, include_winnow=False)
        shared = {f for f in s.features & b.features if f[0] in "sc"}
        self.assertGreaterEqual(len(shared), 3)
        self.assertFalse(b.by_type("f:"), "stripped binaries must not expose function symbols")


class IndexTests(unittest.TestCase):
    def test_keyed_storage_has_no_plaintext(self):
        idx = FingerprintIndex(KEY)
        idx.add("r1", {"s:secret proprietary message", "c:123456"})
        stored = " ".join(idx.records["r1"].hashed)
        self.assertNotIn("secret", stored)

    def test_retrieval_and_open_set_abstain(self):
        idx = FingerprintIndex(KEY)
        rng = random.Random(1)
        specs = [synth.random_program(f"p{i}", rng) for i in range(200)]
        for s in specs:
            idx.add(s.pid, extract_source(synth.render(s)).features)
        hit = idx.search(extract_source(synth.render(specs[42]), include_winnow=False).features)
        self.assertEqual(hit[0].ref, "p42")
        unrelated = extract_source(synth.render(synth.random_program("zz", random.Random(999))), include_winnow=False)
        d = decide(idx.search(unrelated.features), min_score=40.0, min_margin=2.0, min_distinct=3)
        self.assertFalse(d.escalate)

    def test_delete_and_retention(self):
        idx = FingerprintIndex(KEY)
        idx.add("keep", {"s:alpha beta gamma"})
        idx.add("gone", {"s:alpha beta gamma", "c:99999"}, ttl_seconds=1)
        self.assertEqual(idx.purge_expired(now=time.time() + 5), ["gone"])
        self.assertNotIn("gone", idx.records)
        self.assertTrue(idx.delete("keep"))
        self.assertEqual(idx.search({"s:alpha beta gamma"}), [])


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.svc = InvestigationService(FingerprintIndex(KEY), thresholds=Thresholds(min_score=5.0, min_margin=1.0, min_distinct=3))
        self.ing = Principal("pipeline", "ingestor")
        self.inv = Principal("alice", "investigator")
        rng = random.Random(5)
        self.specs = [synth.random_program(f"sess-{i}", rng) for i in range(50)]
        for s in self.specs:
            self.svc.ingest_source(self.ing, s.pid, synth.render(s))

    def test_query_requires_case_and_role(self):
        with self.assertRaises(AccessDenied):
            self.svc.open_case(self.ing, "ticket T-1 approved by counsel", "binary")
        with self.assertRaises(AccessDenied):
            self.svc.investigate(self.inv, "nonexistent", Path(__file__), "source")
        with self.assertRaises(ValueError):
            self.svc.open_case(self.inv, "", "binary")

    @unittest.skipUnless(HAVE_GCC, "gcc/objdump required")
    def test_end_to_end_binary_investigation(self):
        case = self.svc.open_case(self.inv, "Abuse ticket AB-123; policy 4.2 approval", "single binary")
        with tempfile.TemporaryDirectory() as d:
            b = _compile(synth.render(self.specs[7]), Path(d) / "sample", ("-O2",), strip=True)
            report = self.svc.investigate(self.inv, case.case_id, b, "binary")
        self.assertTrue(report["decision"]["escalate"])
        self.assertEqual(report["candidates"][0]["ref"], "sess-7")
        self.assertIsNone(report["classifier_signal"]["score"])
        self.assertTrue(report["limitations"])
        self.assertTrue(self.svc.audit.verify())

    def test_audit_chain_detects_tampering(self):
        log = AuditLog()
        log.append("a", "x")
        log.append("b", "y")
        self.assertTrue(log.verify())
        log.entries[0]["actor"] = "mallory"
        self.assertFalse(log.verify())


if __name__ == "__main__":
    unittest.main()
