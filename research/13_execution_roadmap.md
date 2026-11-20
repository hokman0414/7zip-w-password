# 13 — Execution Roadmap (gated, not time-boxed)

Work is sequenced by **evidence gates**, not by calendar. Each gate has a pass condition and a kill condition. Build investment beyond the existing vertical slice is **locked** until Gate 3 passes.

## Gate 0 — Done (this run)
- Repo inventory: no model, no dataset, no reusable code (E01).
- Vertical slice and synthetic benchmark with measured results (E30a–e).
- SAT package: ACH, KAC, premortem, red team, signposts.
- Simulated persona votes, Rounds 1–2. No consensus.

## Gate 1 — Run three experiments in parallel

| Experiment | Pass | Kill / revise |
|---|---|---|
| **X1 Real-code benchmark.** Use OSS projects as stand-ins for proprietary code. Embed 1–3 real functions or files into other real OSS hosts. Build with the hosts' real build systems (gcc/clang, -O2/-Os, stripped, ARM cross-compile). Index ≥ 10k real files. Measure R@10, escalation recall, and FER on ≥ 1,000 out-of-index real binaries. Exclude shared libraries (zlib, OpenSSL) by df/library suppression. | R@10 ≥ 0.80 on transplanted function-level reuse **and** FER ≤ 1% | R@10 < 0.6, or FER > 1% at any useful threshold → F becomes a services-only offering. Revisit features: decompiler or CFG-based, plus BinDiff-class matching. |
| **X2 Buyer discovery.** Run 12 interviews (doc 10 segment F) with the 20 non-leading questions. Log verbatim notes; record only real responses. | ≥ 4 of 12 recount a binary/firmware case in the last 24 months, **and** ≥ 3 offer test data or a pilot | < 4 of 12, or no data offers → **STOP** F |
| **X3 Counsel opinion on A16.** Cover lawful acquisition and analysis of third-party binaries for infringement detection (US DMCA §1201(f) and interoperability scope, EU Software Directive Art. 6, EULA anti-RE terms, evidentiary chain of custody). | A written opinion that identifies a lawful operating mode, for example customer-acquired artifacts with customer-directed analysis | No lawful mode in the primary market → **STOP** F |
| **Parallel: founder asset validation** (doc 08 protocols) | Assets pass the license, provenance, and leakage checks | Assets fail → C and E stay closed |

## Gate 2 — Re-run the analysis with real evidence
- Update the evidence ledger with X1–X3 results; anonymize interview evidence.
- Re-run the ACH and the KAC, then re-score the premortem.
- Persona Round 3. Votes must cite X1–X3. The gates are unchanged and none are waived.
- **Pass:** all consensus gates pass, or the only failing gates are formally shown to be the wrong gatekeepers *and* that rationale is reviewed by a human.

## Gate 3 — Paid proof-of-concept
- 2 paid PoCs with IP counsel or forensics firms. Each PoC uses the customer's own code and lawfully acquired artifacts, with the key held by the customer.
- Deliverable: an evidence packet reviewed by an independent expert.
- **Pass:** ≥ 2 paid PoCs completed, ≥ 1 packet used in a real decision (cease-and-desist, filing, settlement, or diligence outcome), and an expert endorses its methodology.
- **Only then:** BUILD (doc 12 next increments: PE/Mach-O/ARM, firmware unpacking, location-level exhibits, OIDC/WORM audit).

## Engineering work allowed before Gate 3

These items reduce uncertainty and do not amount to a platform build:
1. X1 harness: real-repo ingestion and an ARM cross-compile path.
2. Library-feature suppression (a known-OSS fingerprint denylist) to cut false positives from shared code.
3. Containment-first scoring for partial reuse.
4. A sample evidence-packet template for expert review (synthetic case only).

## Signposts to watch (doc 05)
- Incumbents add compiled-artifact matching: Cycode, BigID, GitGuardian, or SAFE BitMatch updates. This erodes differentiation (A19).
- Court decisions on early trade-secret identification and on RE-derived evidence admissibility.
- Providers publish artifact-first attribution cases. If they become frequent, re-open the original concept.
