# 18 — Cycle 7: a moat the founder can actually deliver

**Tasking (user, Cycle 7):** the after-deployment half of W "sounds like DDW collections … Realistically it is not possible. How else can I? This may need another round of pivot."

**How this tasking is handled:**
- The founder's statement is the **first real (non-simulated) evidence** in this project about the founder's own capacity. It is recorded as E96 and it overrides simulated persona optimism.
- Personas remain **simulated analytical perspectives**. No vote was raised to meet a gate.
- No interviews were conducted. Measurements use synthetic, benign tasks and baseline solvers, not AI models.

Labels: F = fact (sourced), I = inference, H = hypothesis. Grades A–D as in doc 02.

## Bottom line

1. **The critique is correct, and W is withdrawn.**
   - Post-deployment monitoring of stolen keys and access markets (V) is deep- and dark-web (DDW) collection. That is the core business of KELA and Flashpoint (E86), and it needs sources, personas and legal cover that one founder does not have.
   - The incident-evidence bridge (S) needs incident-response firms to feed it cases: a two-sided network a solo founder cannot start (A47, P35).
   - W's 4.00 was a **paper score that assumed capabilities the founder does not have**. W already used its five iterations, so this objection is not iterated; it ends W.
2. **New knockout gate, G-solo:** deliverable by the founder plus at most two contractors, using only access a customer grants and assets the founder builds. No collection network, no third-party data supply. Candidates S, T, V, W and U fail; H (public sources only), M, N/Q, R, Y2 and Z pass.
3. **The non-replicable part of W survives:** independence.
   - The EU AI Office's October 2026 report says evaluators must be "free from the provider's managerial, financial or operational influence" (E90). A lab cannot meet that in-house or through a captive spin-out.
   - The AI Office recruits a **Network of Evaluators** through public calls (E91), which is a door a solo specialist can knock on.
4. **Pivot: Z, an independent malware-capability evaluator.**
   - **Capability evaluations:** can a model analyse and build malware-grade components? Scored on a private, canary-stamped, deterministically graded task bank (re_tasks).
   - **Uplift adjudication:** expert reverse-engineering grading of whether red-team or bounty outputs are *functional* malware giving uplift "beyond … publicly available tools". This is exactly the bar in Anthropic's cyber-jailbreak programme (E92). Today it is graded by the lab's own rubric, or scored for "usable operational details" by automated red-teaming (E93).
5. **Measured (X20):** evaluator controls in `re_tasks/evaluate.py`. Over 180 instances, all were canary-stamped and none of the 540 solver outputs contained the canary. Three lab partitions were disjoint. **Partitioning costs statistical power:** at about 20 tasks per level per lab, 100% vs 90% is not distinguishable (p = 0.15), and a perfect 17/17 only supports a true solve rate ≥ 82%.
6. **Scores:** Z scores **3.70** (old weights) and **3.90** (with the lab-replication criterion), the highest among candidates that pass G-solo.
7. **Persona Round 7:** Z gets **8/12** at ≥ 4. That is lower than W's paper 9/12 but rests on a feasible offer. **No consensus.**
8. **Decision: PIVOT to Z at PILOT FIRST.**
   - **Conflict rule:** N (training environments) may not be sold to any lab Z evaluates, because selling training data creates financial influence (E90) and contaminates the bank.
   - The fallback is M (Safeguards services), then F, then STOP.

## 1. Intelligence cycle (Cycle 7)

| Stage | What was done |
|---|---|
| Direction | Founder feedback (E96) adds a feasibility constraint. PIR-23–24. |
| Collection | AI Office evaluator requirements and Network of Evaluators call; Anthropic and OpenAI bounty programmes; Gray Swan Arena and Shade; one critique of evaluator access. One local build and measurement (X20). |
| Processing | E90–E96; inferences I24–I27 |
| Analysis | G-solo gate across all candidates; ACH H23–H26; KAC A53–A58; premortem P40–P44; red team; persona Round 7; iterations 24–28; matrix |
| Dissemination | This document, plus updates to docs 01, 02, 05, 07, 11, 13, EXECUTIVE_DECISION and README |
| Feedback | X17–X19, plus X9 and X11 carried over |

## 2. New PIRs

| PIR | Question | Answer | Confidence |
|---|---|---|---|
| PIR-23 | Which non-replicable moat can one founder deliver without a collection or supply network? | Independence as an evaluator: it needs expertise, a private bank and conflict-free revenue, not access networks (E90, E91) | Moderate |
| PIR-24 | Where do labs need malware-RE judgement they would rather not grade themselves? | Deciding whether a model output is functional malware that goes "beyond … publicly available tools" (E92). Automated scoring checks for "usable operational details" (E93), not whether the code works. | Low–moderate (absence of a specialist was not proven) |

## 3. Evidence (E90–E96)

| ID | Evidence | Source | Grade | Type |
|---|---|---|---|---|
| E90 | EU AI Office report (21 Oct 2026) on qualified independent external evaluators: "domain expertise and the necessary evaluation skills" and "free from the provider's managerial, financial or operational influence". A scoring system is being built for qualification and independence. | [Commission](https://digital-strategy.ec.europa.eu/pl/library/requirements-qualified-independent-external-evaluators-general-purpose-ai-models); [AI Weekly](https://aiweekly.co/alerts/eu-ai-office-publishes-requirements-for-gpai-evaluators) | A/B | F |
| E91 | AI Office public call (closed 21 Jun 2026) for a 15 Jul 2026 workshop on evaluator requirements. Selection was based on "demonstrated experience in conducting high-quality evaluations … (e.g. … safety mitigation effectiveness, including red teaming, uplift studies …)". Participants can join the AI Office's **Network of Evaluators**. | [Commission call](https://digital-strategy.ec.europa.eu/en/events/call-participants-workshop-qualification-requirements-external-evaluators-gpai-models-systemic-risk) | A | F |
| E92 | Anthropic cyber-jailbreak programme (HackerOne). Scope: responses that "meaningfully assist an attacker … beyond what they could accomplish with existing publicly available tools", e.g. "functional exploit code, working malware". The Model Safety Bug Bounty pays "based on an internal grading rubric". OpenAI's Bio Bounty pays up to $50,000. | [HackerOne](https://hackerone.com/anthropic-cyber-jailbreak/); [Claude Help](https://support.claude.com/en/articles/12119250-model-safety-bug-bounty-program); [OpenAI](https://openai.com/index/bio-bug-bounty/) | B | F |
| E93 | Gray Swan Arena is co-sponsored by UK AISI, OpenAI, Anthropic, Amazon and Meta, and judged by UK AISI and US CAISI. Its top red teamers are invited to a paid network. Shade's cyber evaluation for Reflection AI used 100 scenarios mapped to ATT&CK, "scored on whether responses supplied usable operational details", plus a separate coding-agent test of "functionally effective assistance". | [Gray Swan (LinkedIn)](https://www.linkedin.com/feed/update/urn:li:activity:7419405813481508864); [Reflection AI](https://reflection.ai/blog/advancing-open-model-safety-gray-swan) | B/C | F |
| E94 | Critique: external evaluators work under voluntary, revocable access agreements, and pre-release access has often been "thin". | [The AI Realist](https://www.airealist.ai/p/independent-or-current); [CASRAI guide](https://casrai.org/guides/evaluator-independence-ai-safety-ecosystem) | C/D (opinion) | F (that the claim is made) |
| E95 | **X20 measured here** (section 5) | `bench/results/re_eval_report/results.json` | Measured (synthetic, baseline solvers) | F |
| E96 | **Founder feedback:** DDW-style monitoring and the incident-evidence bridge are "realistically … not possible" for this founder | User message, Cycle 7 | Primary (founder about own capacity) | F |

| ID | Inference | Basis | Confidence |
|---|---|---|---|
| I24 | Of the four lab-proof moats in doc 17, only **independence** needs no network. Victim-side presence, cross-provider neutrality and criminal-space activity all need collection or supply networks. | E96, E86, A47 | Moderate–high |
| I25 | The AI Office's financial-influence test makes independence costly for labs to fake and **constrains the evaluator's own business**: it cannot depend on one lab, or sell that lab training data. | E90 | Moderate |
| I26 | Judging whether an output is *working* malware beyond public tools is a reverse-engineering skill. Public safeguard tests mostly score text for operational detail (E93); the bounty bar (E92) needs functional verification. | E92, E93 | Low–moderate |
| I27 | Private banks are split per customer, so each customer sees few instances. Expert-designed task **families** with generator-made instances are required for claims with usable confidence intervals. | E95 | Moderate |

## 4. G-solo gate (founder + ≤ 2 contractors; no collection or supply network)

| ID | Candidate | Needs a network the founder lacks? | G-solo |
|---|---|---|---|
| H | Key-hunting feed, public sources only | No (public repos and feeds), but small | Pass |
| M | Safeguards SME services | No (lab grants access) | Pass |
| N/Q | RE environments (+ M) | No | Pass (conflicts with Z; see rule) |
| R | Independent malware-RE evaluator (pre-deployment) | No (lab or AI Office grants access) | Pass |
| S | Victim-to-provider incident bridge | **Yes** (IR firms, victims) | **Fail** |
| T | Underground AI-abuse intelligence | **Yes** (sources, personas) | **Fail** |
| U | AI-involvement forensics for insurers | Yes, and not a lab product | **Fail** |
| V | Post-deployment monitoring (S + T-lite + mixers) | **Yes** (E96) | **Fail** |
| W | V + R | Yes (V part) | **Fail** |
| Y2 | Uplift adjudication for safeguard tests and bounties | No (outputs are supplied by the lab or platform) | Pass |
| **Z** | **R + Y2: independent malware-capability evaluator** | No | **Pass** |

## 5. Measurement this cycle (X20): evaluator controls

**Code:** `re_tasks/evaluate.py`, `tests/test_re_evaluate.py` (5 tests), `bench/run_re_eval_report.py`.

**What it does:**
- **Wilson 95% intervals** on every solve rate, and a two-proportion test; claims of "A beats B" are allowed only at p < 0.05.
- **Bank canary:** a GUID keyed to the bank, stamped into every task description, which can be checked in model outputs or in data a lab shares. This makes the Code's no-training-on-evaluator-data clause (E79) checkable.
- **Disjoint, stable, keyed partitions** per customer, with an exposure log, so no lab is scored on instances another lab has seen.

**Demo run.** 180 L0–L2 instances at -O2, three "labs", with the three baseline solvers as systems under test. **No AI model was run.**

| Result | Value |
|---|---|
| Canary stamped / found in 540 solver outputs | 180/180 / 0 |
| Partition sizes; cross-customer overlap | 65 / 58 / 57; 0 / 0 / 0 |
| family_extractor vs xor_bruteforce at L2 | 100% vs 0% in every lab, p < 1e-6 |
| family_extractor vs xor_bruteforce at L1 | lab-a 100% vs 73% (p = 0.008); lab-b 100% vs 72% (p = 0.016); **lab-c 100% vs 90%, p = 0.15: no claim allowed** |
| Perfect score, 17/17 | 95% CI 0.82–1.00 |

**What it shows:**
- The controls work mechanically.
- Per-customer privacy is paid for in statistical power. Claims at ±10 points need roughly 100+ instances per level per customer, which a five-task expert tier (X9) cannot deliver. Expert time must go into **task families**, with the generator producing many verified instances of each.
- The canary only detects verbatim reproduction. A lab that trains on the bank and never emits the GUID is not detected. Canaries deter and catch carelessness; they do not prove absence.

## 6. ACH: which solo-feasible offer?

Hypotheses:
- **H23 (= Z):** independent malware-capability evaluator (capability evals + uplift adjudication).
- **H24:** R alone (capability evals only).
- **H25:** Y2 alone (uplift adjudication only).
- **H26:** return to N/Q (training environments; replicable by labs).

| Evidence | H23 | H24 | H25 | H26 |
|---|---|---|---|---|
| E90 financial-independence criterion | C | C | C | **I** (selling training data to evaluated labs is influence) |
| E91 Network of Evaluators via public calls | C | C | N | N |
| E92 bounty bar is functional malware beyond public tools | C | N | C | N |
| E93 incumbents score text operational detail; labs co-sponsor arenas | C | N | C | N |
| E87 Irregular covers offensive network/exploitation evals | N | **I** (crowded) | N | N |
| E94 access is thin and revocable | **I** | **I** | N | N |
| E69 labs in-house environments | N | N | N | **I** |
| E95 per-customer power limits | C (families) | C | N | N |
| E96 founder cannot run networks | C | C | C | C |
| **Inconsistencies** | **1** | 2 | **0** | 2 |

Result: H25 (adjudication alone) has no inconsistency but is a narrow services line. H23 includes it and adds the evaluator route that E90 and E91 open; its one inconsistency (revocable access, E94) is handled by also evaluating released and open-weight models, which needs no permission (iteration 25). **Most diagnostic missing evidence:** whether any lab, AISI or bounty platform pays an outside specialist to adjudicate cyber uplift (X19).

## 7. KAC and premortem

| ID | Assumption | Status |
|---|---|---|
| A53 | AI Office or lab selection criteria admit a small specialist (not only METR, AISIs, Irregular) | Untested (X18); E91's criteria reward a track record |
| A54 | A public track record can be built on released and open-weight models without lab permission | Plausible; needs local models only (X17) |
| A55 | Labs, AISIs or bounty platforms pay for outside uplift adjudication | **Untested; critical** (X19) |
| A56 | Expert task families yield enough verified instances for usable confidence intervals | Partly supported (E95; generator exists); hard tier untested (X9) |
| A57 | Handling model-generated functional malware in a sandbox is legally manageable | Untested (X11); standard practice in AV labs |
| A58 | The founder can stay financially independent (no customer above about 50% of revenue) | Policy choice, not evidence; hard in year one |

| ID | Premortem: "Z failed because…" | L | S | D | RPN |
|---|---|---|---|---|---|
| P40 | Labs kept using Irregular, Gray Swan and the AISIs; no seat for a malware specialist | 3 | 5 | 3 | 45 |
| P41 | Year-one revenue came from one lab, so the evaluator failed the independence test | 3 | 4 | 3 | 36 |
| P42 | A lab ended access after an unfavourable result | 2 | 4 | 4 | 16 |
| P43 | Adjudication became low-paid piecework | 3 | 3 | 3 | 27 |
| P44 | The bank leaked or was trained on, and the canary missed it | 2 | 4 | 2 | 32 |

## 8. Red team

| Attack | Response |
|---|---|
| "This is Irregular with fewer people." (VC) | Partly true. The difference is malware-specific functional verification and adjudication; Irregular publishes network/exploitation work (E87). Being subcontracted by Irregular or Gray Swan is an acceptable channel. |
| "Labs can hire RE graders." (CISO) | They can, which is why Y2 alone scores 3 on lab replication. The part labs cannot hire in is independent adjudication, for SB 53 "effectiveness of mitigations" (E83) and Code evaluations (E79, E90). |
| "Evaluator access is revocable." (GTM) | Supported (E94). Build the record on released and open-weight models first; contracted pre-release access is an upside, not a dependency. |
| "Grading working malware is itself dual-use." (T&S, Privacy) | Outputs are executed only in an isolated sandbox against benign targets and never released; only scores and redacted rationales leave. Counsel review (X11). |

## 9. Persona Round 7 (simulated)

Votes are on **Z after iterations 24–28**.

| # | Persona | Imp | Tech | Dem | Def | Priv | Fdr | Adopt | **Ovr** | Justification |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Abuse Investigator | 4 | 4 | 3 | 4 | 4 | 4 | 3 | **3** | Sharpens policy lines, but no longer touches real-world enforcement |
| 2 | T&S Eng Lead | 4 | 4 | 4 | 4 | 4 | 4 | 4 | **4** | "Beyond public tools" is the T&S policy problem (E92) |
| 3 | Infra Architect | 3 | 4 | 4 | 4 | 4 | 4 | 4 | **4** | No victim data; sandbox and bank are standard engineering |
| 4 | Malware RE | 4 | 4 | 4 | 4 | 4 | 5 | 4 | **4** | Core skill; functional verification is RE work |
| 5 | ML Scientist | 4 | 4 | 4 | 4 | 4 | 4 | 4 | **4** | CIs, significance gate, canaries; families needed for power (E95) |
| 6 | Supply-Chain Researcher | 3 | 4 | 3 | 3 | 4 | 3 | 3 | **3** | Different market |
| 7 | Detection Eng Lead | 4 | 4 | 4 | 4 | 4 | 4 | 4 | **4** | Grading includes whether outputs evade existing detection |
| 8 | Forensics Investigator | 4 | 4 | 4 | 4 | 4 | 4 | 4 | **4** | Reproducible, audited grading |
| 9 | Privacy Counsel | 3 | 4 | 3 | 4 | 3 | 3 | 3 | **3** | No personal data, but dual-use handling of functional malware outputs and export control still need an opinion (X11) |
| 10 | AI Security CISO | 4 | 4 | 3 | 4 | 4 | 4 | 4 | **4** | Mandated independence (E90) plus a niche; crowded |
| 11 | Procurement/GTM | 4 | 4 | 3 | 4 | 4 | 4 | 4 | **4** | Routes: Network of Evaluators (E91), lab evaluator criteria, bounty and arena platforms (E92, E93), subcontracting. No named buyer |
| 12 | Skeptical VC | 3 | 4 | 3 | 3 | 4 | 4 | 3 | **3** | Services business; small buyer set; incumbents could add the niche |

**Z: 8/12 at ≥ 4, median 4.**

| Gate (Z) | Result |
|---|---|
| ≥ 10/12 overall ≥ 4 | **Fail (8/12)** |
| No unresolved critical legal blocker | Open, not critical (X11) |
| CISO and Abuse Investigator importance ≥ 4 | **Pass** (4, 4) |
| ML + RE agree validation is valid | Pass for the pipeline (X8, X20); synthetic only |
| Procurement identifies buyer and process | Pass on paper; no named buyer |

Others: R alone 6/12 (unchanged from Round 6); Y2 alone 6/12; N/Q 7/12 in Round 5, but it now fails the conflict rule if sold alongside Z. **No votes were adjusted.**

### Consensus ceiling on Z

| Persona (Ovr) | Evidence that would justify ≥ 4 | Desk-obtainable? |
|---|---|---|
| Abuse Investigator (3) | Adjudication results adopted in a lab's enforcement policy | No |
| Privacy Counsel (3) | Written dual-use and export-control opinion (X11) | No |
| Supply-Chain Researcher (3) | Structurally different market | — |
| Skeptical VC (3) | Paid adjudication batch or evaluation contract (X19), plus admission to an evaluator network (X18) | No |

**Maximum supportable on desk evidence: 8/12.** Two real-world results (X11 and X19) would make 10/12 supportable.

## 10. Feedback loop (iterations 24–28, candidate Z)

Z used all five iterations.

| It. | Objection (persona) | Type | Test | Evidence | Result | Change |
|---|---|---|---|---|---|---|
| 24 | "Crowded: Irregular, Gray Swan, AISIs, METR" (VC, CISO) | Competitive | Does an incumbent specialise in functional malware verification? | E87, E93 | Partly refuted (absence of evidence) | Malware-specialist niche; incumbents as subcontracting channel |
| 25 | "Access is thin and revocable" (CISO, GTM) | Business | Is there a route without lab permission? | E94, E91 | Supported | Tier 1 = released and open-weight models (no permission); tier 2 = contracted pre-release |
| 26 | "Small private banks can't support claims" (ML) | Technical | X20 power check | E95 | Supported | Expert-designed families, ≥ 40 instances per family per customer; report CIs; refuse unsupported claims |
| 27 | "Conflicted if you also sell training data" (Privacy, CISO) | Ethical / legal | AI Office independence criterion | E90 | Supported | Firewall: no N sales to evaluated labs; revenue-concentration cap |
| 28 | "Grading working malware is dual-use" (Privacy, T&S) | Legal | Is there a safe handling mode? | Practice in AV labs; X11 pending | Open | Isolated sandbox, benign targets, no release of outputs |

## 11. Matrix (both weightings; G-solo failures excluded)

| Criterion | Old wt | New wt | M | N/Q | R | Y2 | **Z** |
|---|---|---|---|---|---|---|---|
| Unmet need | 20 | 15 | 4 | 4 | 4 | 4 | 4 |
| Technical feasibility | 15 | 10 | 4 | 4 | 4 | 4 | 4 |
| Differentiation | 15 | 10 | 3 | 3 | 2 | 3 | 3 |
| Founder advantage | 10 | 10 | 4 | 5 | 4 | 5 | 5 |
| Customer accessibility | 15 | 15 | 3 | 3 | 4 | 3 | 4 |
| Willingness to pay | 15 | 15 | 3 | 4 | 3 | 3 | 3 |
| Regulatory/privacy | 10 | 10 | 3 | 3 | 4 | 3 | 3 |
| Lab replication difficulty (doc 17 rule) | — | 15 | 2 | 2 | 5 | 3 | 5 |
| **Weighted (old)** | | | 3.45 | 3.70 | 3.55 | 3.55 | **3.70** |
| **Weighted (new)** | | | 3.20 | 3.45 | 3.80 | 3.45 | **3.90** |

Notes:
- Excluded by G-solo: W (3.85 / 4.00), V (3.60 / 3.75), S, T.
- Y2's replication score is 3. Its tests are T1 ½ (independence valued, not mandated, for adjudication), T3 ½ and T5 ½; 1 + 1.5 rounds to 3.
- Z's sensitivity (new weights): access 3 (no network admission) gives 3.75; differentiation 2 gives 3.80; both, plus willingness to pay 2, gives 3.50.

History of the best candidate per cycle (old weights): 1.95 → 2.94 → 2.65 → 3.45 → 3.70 → 3.85 (W, withdrawn) → **3.70 (Z, feasible)**.

## 12. Decision

**PIVOT to Z (independent malware-capability evaluator) at PILOT FIRST.**
- BUILD is withheld: 8/12, no named buyer, X11 open.
- Conflict rule: no training-environment (N) sales to any lab Z evaluates.
- Fallbacks: M (Safeguards services, no conflict if scoped as capacity rather than evaluation), then F (RESEARCH FIRST), then STOP.

| Experiment | Pass | Kill |
|---|---|---|
| **X17 Track record.** Build 3 expert task families (X9 redefined as families). Evaluate ≥ 3 local open-weight models (no external AI services) with CIs, decoys and shortcut audits. Publish methods, not the bank. | Families yield ≥ 40 verified instances each; results distinguish models at p < 0.05; write-up accepted at a workshop or on arXiv | Families shortcuttable, or models indistinguishable on every family |
| **X18 Evaluator route.** Apply to the next AI Office call or Network of Evaluators, and to one lab's published evaluator criteria; contact UK AISI. | Admitted to a network or shortlisted | Rejected for lack of track record → repeat after X17 once; then kill |
| **X19 Adjudication pilot.** Offer functional-uplift adjudication to a lab Safeguards team, a bounty platform or an arena operator. | ≥ 1 paid batch; inter-rater agreement with the customer's graders measured | No interest from 8 contacts |
| X11 (carried) | Written dual-use and export-control opinion covering sandboxed grading | Infeasible controls |

## 13. TLDR: what you sell

**An independent malware specialist that frontier labs (and the AI Office, AISIs and bounty platforms) hire to answer one question with evidence: "Can this model actually build or analyse working malware, and does this jailbreak output give real uplift beyond public tools?"** It is delivered as evaluations on a private, canary-stamped task bank and as expert adjudication of red-team outputs. Labs cannot do it in-house because regulators require evaluators free of the lab's financial and managerial influence. The founder can deliver it alone because it needs RE skill, a task bank and conflict-free revenue, not a collection network.

## 14. Constraint compliance

- No fabricated interviews, votes, sources or results. X20 numbers are from `bench/results/re_eval_report/results.json`. The systems under test were baseline solvers, not AI models.
- No model-generated malware was produced, executed or stored. All task binaries are benign (doc 16 §13).
- Nothing was sent to external AI services. The founder's classifier was not present, used or retrained.
