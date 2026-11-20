"""Benchmark the consent-gated incident packet broker on synthetic incidents.

Every incident is generated here; no real victim data is used. Each log plants
victim identifiers of several kinds, including kinds the redactor is NOT
designed to catch (unlisted person names, IPv6, external cloud hostnames), so
the residual leak rate is measured rather than assumed.

Metrics
  leak rate per identifier kind      planted value appears in any packet
  neutrality violations              a packet mentions another provider's
                                     endpoint, model, key suffix or name
  routing recall                     provider used in the incident gets a packet
                                     containing its indicator
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from provenance.incident_packet import IncidentBroker, VictimConsent  # noqa: E402
from provenance.service import Principal  # noqa: E402
from tests.test_llm_indicators import fake_anthropic, fake_openai  # noqa: E402

FIRST = ["Jane", "Omar", "Li", "Priya", "Tomas", "Ana", "Kofi", "Mei", "Lars", "Sofia"]
LAST = ["Roe", "Haddad", "Wei", "Nair", "Novak", "Silva", "Mensah", "Tanaka", "Berg", "Rossi"]
ORGS = ["Northwind", "Contoso", "Fabrikam", "Tailspin", "Wingtip", "Litware"]
PROVIDERS = {
    "openai": ("api.openai.com", "gpt-4o", fake_openai),
    "anthropic": ("api.anthropic.com", "claude-sonnet-4", fake_anthropic),
}
INV = Principal("bench", "investigator")


def incident(i: int, rng: random.Random, list_names: bool):
    org = rng.choice(ORGS)
    dom = f"{org.lower()}-{i}.example"
    people = [f"{rng.choice(FIRST)} {rng.choice(LAST)}" for _ in range(2)]
    user = people[0].split()[0][0].lower() + people[0].split()[1].lower()
    ip = f"10.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"
    ip6 = f"fd00:{rng.randint(4096, 65535):x}::{rng.randint(1, 65535):x}"
    cloud = f"bkt-{rng.randrange(16**8):08x}.s3.amazonaws.com"
    used = rng.sample(sorted(PROVIDERS), rng.choice([1, 2]))
    keys = {p: PROVIDERS[p][2](i * 10 + k) for k, p in enumerate(used)}
    lines = [
        f"2026-04-{1 + i % 28:02d}T08:00:00Z {org.upper()[:8]}\\{user} logon from {ip} to dc01.{dom}",
        f"2026-04-{1 + i % 28:02d}T08:03:00Z C:\\Users\\{user}\\AppData\\Local\\svc.exe started",
        f"2026-04-{1 + i % 28:02d}T08:04:00Z ipv6 peer {ip6} contacted",
        f"2026-04-{1 + i % 28:02d}T08:06:00Z staging upload to https://{cloud}/dump.7z",
        f"2026-04-{1 + i % 28:02d}T08:07:00Z email to {user}@{dom} cc {people[1].replace(' ', '.').lower()}@{dom}",
        f"2026-04-{1 + i % 28:02d}T08:08:00Z note: {people[0]} and {people[1]} of {org} confirmed exfiltration",
    ]
    for p in used:
        host, model, _ = PROVIDERS[p]
        lines.append(f"2026-04-{1 + i % 28:02d}T08:05:00Z svc.exe POST https://{host}/v1 model={model} key={keys[p]}")
    planted = {
        "ipv4": [ip], "internal_host": [f"dc01.{dom}", dom], "account": [f"{org.upper()[:8]}\\{user}"],
        "user_path": [f"Users\\{user}"], "email": [f"{user}@{dom}"], "org_name": [org],
        "person_name": people, "ipv6": [ip6], "external_cloud_host": [cloud],
        "credential": list(keys.values()),
    }
    consent = VictimConsent(
        case_id=f"case{i}", granted_by="victim", providers=frozenset(PROVIDERS),
        internal_domains=(dom,), sensitive_terms=tuple([org] + (people if list_names else [])),
        harm_summary=f"{org} data exfiltrated",
    )
    return consent, lines, used, planted


def run(n: int, seed: int, list_names: bool) -> dict:
    rng = random.Random(seed)
    leaks: dict[str, list[int]] = {}
    neutrality = routed = expected = 0
    for i in range(n):
        consent, lines, used, planted = incident(i, rng, list_names)
        broker = IncidentBroker(pseudonym_key=b"k" * 32, fingerprint_key=b"f" * 32)
        broker.record_consent(INV, consent)
        packets = broker.build_packets(INV, consent.case_id, {}, lines)
        blob = json.dumps(packets).lower().replace("\\\\", "\\")
        for kind, values in planted.items():
            hits = sum(v.lower() in blob for v in values)
            leaks.setdefault(kind, [0, 0])
            leaks[kind][0] += hits
            leaks[kind][1] += len(values)
        for p in used:
            expected += 1
            host, model, _ = PROVIDERS[p]
            if p in packets and model in json.dumps(packets[p]):
                routed += 1
        for p, pkt in packets.items():
            text = json.dumps(pkt).lower().replace(f'"provider": "{p}"', "")
            for other, (host, model, _) in PROVIDERS.items():
                if other != p and (host in text or model in text or other in text):
                    neutrality += 1
        if not broker.audit.verify():
            raise SystemExit("audit chain broken")
    return {
        "incidents": n,
        "victim_lists_person_names": list_names,
        "leak_rate": {k: round(h / t, 3) for k, (h, t) in sorted(leaks.items())},
        "leaked_over_planted": {k: f"{h}/{t}" for k, (h, t) in sorted(leaks.items())},
        "neutrality_violations": neutrality,
        "routing_recall": round(routed / expected, 3),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=6)
    ap.add_argument("--out", default="bench/results/incident_packet/results.json")
    args = ap.parse_args()
    results = {
        "data": "synthetic incidents generated by this script; no real victim data",
        "without_name_list": run(args.n, args.seed, False),
        "with_name_list": run(args.n, args.seed, True),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
