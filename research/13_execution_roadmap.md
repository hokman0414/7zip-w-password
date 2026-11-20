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

## Cycle 4 track — frontier-lab SME services (candidate M, PILOT FIRST; doc 15)

This track runs ahead of F because the founder's stated customer is frontier AI labs. It needs no further platform build.

| Gate | Work | Pass | Kill |
|---|---|---|---|
| L0 (done) | `provenance/llm_indicators.py`, tests, X4 benchmark (E66, E67) | — | — |
| L1 | Counsel review of the disclosure-only credential protocol (A35); founder conflict check (P27) | Written protocol; no conflicts | Protocol requires holding full keys |
| L2 | **X5** public-data hunting pilot (60 days; no VirusTotal licence; human RE confirms behaviour). **X6** 10 lab conversations (doc 15 §14). **X7** model-attribution lead benchmark on locally generated benign scripts. | X5: ≥ 10 novel T1 samples and ≥ 2 providers act. X6: ≥ 3 describe a capacity gap and ≥ 1 offers a trial case. X7: open-set AUROC ≥ 0.80 after transformations. | X5 and X6 both fail → labs are not viable; return to F / STOP. X7 fail → drop the T3 tier only. |
| L3 | One trial case or retainer with one lab, under its custody | Deliverable used in an enforcement decision; a second engagement requested | No follow-on |
| L4 | Only then: provider-hosted tooling (L) and, optionally, J/K expansions | — | — |

## Cycle 5 track — malware-RE environments for labs (N, sold as Q; PILOT FIRST; doc 16)

This is now the lead track. The Cycle 4 lab track (X5/X6) runs alongside it as Q's Safeguards component.

| Gate | Work | Pass | Kill |
|---|---|---|---|
| R0 (done) | `re_tasks/` generator, grader, baselines; X8 calibration (E78) | — | — |
| R1 | **X11** counsel: dual-use / export-control and benign-payload policy; task IP terms | Written policy | Infeasible controls |
| R2 | **X9** hard-tier pilot: 5 expert tasks, local open-weight baseline, human solve times, shortcut audit. **X10** 10 lab conversations plus 3 data vendors. | X9: ≥ 3/5 resist the baseline, are human-solvable, and show no shortcut. X10: ≥ 2 NDA sample requests and ≥ 1 paid batch or subcontract. | X10 < 1 sample request and vendors decline → fall back to M, else F, else STOP |
| R3 | First paid task batch delivered and accepted by QA | Repeat order | Rejected batch (P31) |
| R4 | Only then: scale the generator, expert network, and Safeguards add-on (Q) | — | — |

Doc 16's consensus-ceiling table lists what each holdout needs. Since Cycle 6 this track is the fallback (Q) and supplies W's pre-deployment task bank (X9).

## Cycle 6 track — independent cyber-misuse assurance for labs (W; withdrawn in Cycle 7; doc 17)

This was the lead track in Cycle 6. X5 (public-data hunting) becomes W's post-deployment monitoring feed; X9 (hard RE tier) becomes its private evaluation bank.

| Gate | Work | Pass | Kill |
|---|---|---|---|
| W0 (done) | `provenance/incident_packet.py`: consent-gated, provider-neutral Measure 9.2-shaped packets; X12 benchmark (E89) | — | — |
| W1 | **X16** counsel: DPIA and lawful basis for edge mode, US transfer, independence definition (A46), SB 53 public-report route | Written opinion and template | Controls make edge mode infeasible |
| W2 | **X13** evaluator route (App. 3.5 criteria / public calls). **X14** 5 IR firms, MSSPs or insurers. **X15** 8 non-Google signatory conversations. | X13: criteria admit a specialist or a call is open. X14: ≥ 2 pilot on a past consented case. X15: ≥ 2 sample-packet requests and ≥ 1 pilot. | X15 fails → fall back to Q; X14 fails → drop S, keep R + monitoring (V without victim packets) |
| W3 | One pilot: a packet set or evaluation used by a lab in a report or decision | Second engagement | No follow-on |
| W4 | Only then: edge-mode packaging for IR firms, monitoring feed at scale, hard-tier bank | — | — |

Superseded in Cycle 7: the founder reports W's post-deployment half is not deliverable (E96). Round 7 voted on Z instead.

## Signposts to watch (doc 05)
- Incumbents add compiled-artifact matching: Cycode, BigID, GitGuardian, or SAFE BitMatch updates. This erodes differentiation (A19).
- Court decisions on early trade-secret identification and on RE-derived evidence admissibility.
- Providers publish artifact-first attribution cases. If they become frequent, re-open the original concept.

## Cycle 7 track — independent malware-capability evaluator (Z; PILOT FIRST; doc 18)

This replaces the Cycle 6 track. W is withdrawn on founder feedback (E96); W0 (`incident_packet`) is kept as a reference implementation only.

| Gate | Work | Pass | Kill |
|---|---|---|---|
| Z0 (done) | `re_tasks/evaluate.py`: Wilson CIs, significance gate, bank canaries, disjoint per-customer partitions; X20 (E95) | — | — |
| Z1 | **X11** counsel: dual-use and export control for sandboxed grading of model-generated malware | Written opinion | Infeasible controls |
| Z2 | **X17** 3 expert task families; ≥ 3 local open-weight models; publish methods (not the bank) | ≥ 40 verified instances per family; models distinguishable at p < 0.05; write-up accepted | Shortcuttable or indistinguishable |
| Z3 | **X18** AI Office call / Network of Evaluators, one lab's evaluator criteria, UK AISI. **X19** adjudication pilot with a lab Safeguards team, bounty platform or arena operator. | X18 admitted or shortlisted; X19 ≥ 1 paid batch with inter-rater agreement measured | X19 no interest from 8 contacts → fall back to M |
| Z4 | Only then: contracted pre-release evaluations; second customer before any customer exceeds ~50% of revenue | — | — |

Re-vote (Round 8) after Z3.
