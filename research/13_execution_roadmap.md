# 13 — Execution Roadmap (gated, not time-boxed)

Work is sequenced by **evidence gates**, not by calendar. Each gate has a pass condition and a kill condition. Build investment beyond the existing vertical slice is **locked** until Gate 3 passes.

## Gate 0 — Done (this run)
- Repo inventory: no model, no dataset, no reusable code (E01).
- Vertical slice and synthetic benchmark with measured results (E30a–e).
- SAT package: ACH, KAC, premortem, red team, signposts.
- Simulated persona votes, Rounds 1–2. No consensus.

## Gate 1 — Run three experiments in parallel

*F status: **RESEARCH FIRST** (Cycle 3). X1 gates any pilot. X2 and X3 run in parallel because they are cheap and independent.*

| Experiment | Pass | Kill / revise |
|---|---|---|
| **X1 Real-binary benchmark (revised in Cycle 3; doc 14 §8).** (a) FSE 2026 public binary TPL benchmark (E35) for comparability. (b) A proprietary-like split: real OSS functions transplanted into unrelated real hosts; stripped; x86_64 and ARM; known-OSS feature suppression. Baselines: B2SFinder, BAT/BANG, our scoring-only slice. Candidate system: slice plus a **local** evidence-verification stage (no external AI service). | Recall ≥ 0.80 **and** precision ≥ 0.95 on the proprietary-like split; false-escalation rate ≤ 1% on out-of-index binaries | Precision < 0.90 after verification, or recall < 0.60 → F becomes services-only or STOP |
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

0. A **local verification stage** after retrieval: identity markers, known-OSS feature suppression for AFC-style filtration, and cross-feature consistency. The design follows the retrieve-then-verify result in E36 and must use local models only.

These items reduce uncertainty and do not amount to a platform build:
1. X1 harness: real-repo ingestion and an ARM cross-compile path.
2. Library-feature suppression (a known-OSS fingerprint denylist) to cut false positives from shared code.
3. Containment-first scoring for partial reuse.
4. A sample evidence-packet template for expert review (synthetic case only).

## Signposts to watch (doc 05)
- Incumbents add compiled-artifact matching: Cycode, BigID, GitGuardian, or SAFE BitMatch updates. This erodes differentiation (A19).
- Court decisions on early trade-secret identification and on RE-derived evidence admissibility.
- Providers publish artifact-first attribution cases. If they become frequent, re-open the original concept.
