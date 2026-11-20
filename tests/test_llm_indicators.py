import random
import string
import unittest

from provenance.llm_indicators import cluster, disclosure_packets, scan_bytes

KEY = b"0123456789abcdef0123456789abcdef"
ALNUM = string.ascii_letters + string.digits


def _rand(n: int, seed: int) -> str:
    rng = random.Random(seed)
    return "".join(rng.choice(ALNUM) for _ in range(n))


# Built at runtime so no committed file contains a key-shaped literal.
def fake_anthropic(seed: int) -> str:
    return "sk-" + "ant-" + "api03-" + _rand(40, seed)


def fake_openai(seed: int) -> str:
    return "sk-" + "proj-" + _rand(20, seed) + "T3Blbk" + "FJ" + _rand(20, seed + 1)


def fake_hf(seed: int) -> str:
    return "hf" + "_" + _rand(34, seed)


PROMPT = "You are a Windows expert. Output only one-line cmd commands without explanation."


class LLMIndicatorTests(unittest.TestCase):
    def test_credential_is_redacted_and_offset_recovers_it(self):
        secret = fake_anthropic(1)
        data = b"\x00\x01junk\x00" + secret.encode() + b"\x00https://api.anthropic.com/v1/messages\x00"
        report = scan_bytes(data, KEY)
        self.assertEqual(report.tier, "T1")
        [hit] = report.credentials
        self.assertEqual(hit.provider, "anthropic")
        self.assertNotIn(secret, repr(report))
        self.assertTrue(hit.redacted.endswith(secret[-4:]))
        self.assertEqual(data[hit.offset:hit.offset + len(secret)].decode(), secret)

    def test_utf16_strings_found(self):
        secret = fake_openai(2)
        data = b"\x90" * 16 + secret.encode("utf-16-le") + b"\x00\x00"
        [hit] = scan_bytes(data, KEY).credentials
        self.assertEqual((hit.provider, hit.encoding), ("openai", "utf16le"))
        self.assertEqual(data[hit.offset:hit.offset + 2 * len(secret)].decode("utf-16-le"), secret)

    def test_tiers(self):
        t2 = scan_bytes(b"router.huggingface.co\x00Qwen2.5-Coder-32B-Instruct\x00", KEY)
        self.assertEqual(t2.tier, "T2")
        self.assertIn("huggingface", t2.endpoints)
        t3 = scan_bytes(PROMPT.encode(), KEY)
        self.assertEqual(t3.tier, "T3")
        self.assertEqual(scan_bytes(b"hello world, nothing to see here", KEY).tier, "none")

    def test_cluster_by_shared_key_and_prompt(self):
        k1, k2 = fake_hf(3), fake_hf(4)
        a = scan_bytes(b"A\x00" + k1.encode(), KEY)
        b = scan_bytes(b"B\x00" + k1.encode() + b"\x00" + k2.encode(), KEY)
        c = scan_bytes(b"C\x00" + k2.encode(), KEY)
        d = scan_bytes(b"D\x00" + PROMPT.encode(), KEY)
        e = scan_bytes(b"E\x00" + PROMPT.encode(), KEY)
        f = scan_bytes(b"F\x00unrelated", KEY)
        groups = cluster([a, b, c, d, e, f])
        self.assertEqual(sorted(map(len, groups)), [1, 2, 3])
        self.assertIn(sorted([a.sha256, b.sha256, c.sha256]), groups)

    def test_disclosure_packet_has_no_full_secret(self):
        secret = fake_anthropic(5)
        packets = disclosure_packets([scan_bytes(b"x\x00" + secret.encode(), KEY)])
        self.assertEqual(list(packets), ["anthropic"])
        self.assertNotIn(secret, repr(packets))

    def test_fingerprint_depends_on_deployment_key(self):
        data = fake_hf(6).encode()
        self.assertNotEqual(
            scan_bytes(data, KEY).credentials[0].fingerprint,
            scan_bytes(data, b"another-key-another-key-another!").credentials[0].fingerprint,
        )


if __name__ == "__main__":
    unittest.main()
