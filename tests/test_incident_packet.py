import json
import unittest

from provenance.incident_packet import IncidentBroker, VictimConsent
from provenance.service import AccessDenied, Principal
from tests.test_llm_indicators import fake_anthropic, fake_openai

INV = Principal("ana", "investigator")


def make_case(providers=("anthropic", "openai"), expires_at=float("inf")):
    broker = IncidentBroker(pseudonym_key=b"p" * 32, fingerprint_key=b"f" * 32)
    consent = VictimConsent(
        case_id="c1", granted_by="victim-ciso", providers=frozenset(providers),
        internal_domains=("acme-corp.example",), sensitive_terms=("Jane Roe", "Acme Corp"),
        harm_summary="Acme Corp payroll data exfiltrated", expires_at=expires_at,
    )
    broker.record_consent(INV, consent)
    a_key, o_key = fake_anthropic(7), fake_openai(8)
    sample = b"\x00" + a_key.encode() + b"\x00https://api.anthropic.com/v1/messages\x00claude-sonnet-4\x00"
    logs = [
        f"2026-03-01T10:00:00Z ACME\\jroe logged in from 10.1.2.3 to fs01.acme-corp.example",
        f"2026-03-01T10:05:00Z C:\\Users\\jroe\\AppData\\x.exe POST https://api.openai.com/v1/chat key={o_key} model=gpt-4o",
        "2026-03-01T10:09:00Z mail from jane.roe@acme-corp.example: Jane Roe approved transfer",
    ]
    return broker, {"x.exe": sample}, logs, a_key, o_key


class IncidentPacketTests(unittest.TestCase):
    def test_requires_consent_and_role(self):
        broker = IncidentBroker(pseudonym_key=b"p" * 32, fingerprint_key=b"f" * 32)
        with self.assertRaises(AccessDenied):
            broker.build_packets(INV, "c1", {}, [])
        broker, arts, logs, *_ = make_case(expires_at=100.0)
        with self.assertRaises(AccessDenied):
            broker.build_packets(INV, "c1", arts, logs, now=200.0)
        with self.assertRaises(AccessDenied):
            broker.build_packets(Principal("eve", "auditor"), "c1", arts, logs, now=50.0)
        self.assertTrue(broker.audit.verify())

    def test_no_victim_identifier_or_full_key_leaks(self):
        broker, arts, logs, a_key, o_key = make_case()
        blob = json.dumps(broker.build_packets(INV, "c1", arts, logs))
        for secret in ["10.1.2.3", "jroe", "jane.roe", "acme-corp", "Jane Roe", "Acme Corp", "ACME\\", a_key, o_key]:
            self.assertNotIn(secret.lower(), blob.lower(), secret)

    def test_each_provider_sees_only_its_own_indicators(self):
        broker, arts, logs, *_ = make_case()
        packets = broker.build_packets(INV, "c1", arts, logs)
        self.assertEqual(set(packets), {"anthropic", "openai"})
        a, o = json.dumps(packets["anthropic"]), json.dumps(packets["openai"])
        self.assertIn("claude-sonnet-4", a)
        self.assertNotIn("openai", a.replace('"provider": "anthropic"', ""))
        self.assertNotIn("gpt-4o", a)
        self.assertIn("gpt-4o", o)
        self.assertNotIn("anthropic", o)
        self.assertEqual(packets["openai"]["period"], {"start": "2026-03-01T10:00:00Z", "end": "2026-03-01T10:09:00Z"})

    def test_provider_outside_consent_is_withheld_and_pseudonyms_are_stable(self):
        broker, arts, logs, *_ = make_case(providers=("anthropic",))
        packets = broker.build_packets(INV, "c1", arts, logs)
        self.assertEqual(set(packets), {"anthropic"})
        self.assertIn("withheld", [e["action"] for e in broker.audit.entries])
        consent = broker.consents["c1"]
        self.assertEqual(broker.redact("c1", "jane.roe@acme-corp.example", consent),
                         broker.redact("c1", "JANE.ROE@acme-corp.example", consent))
        self.assertNotEqual(broker.redact("c1", "10.0.0.1", consent), broker.redact("c2", "10.0.0.1", consent))

    def test_ipv6_redacted_without_touching_timestamps(self):
        broker, *_ = make_case()
        out = broker.redact("c1", "2026-03-01T10:00:00Z peer fd00:1a2b::7 and ::1", broker.consents["c1"])
        self.assertIn("2026-03-01T10:00:00Z", out)
        self.assertNotIn("fd00:1a2b::7", out)
        self.assertNotIn("::1", out)


if __name__ == "__main__":
    unittest.main()
