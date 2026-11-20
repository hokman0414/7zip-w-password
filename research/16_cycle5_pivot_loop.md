# 16 — Cycle 5: keep pivoting toward persona consensus

**Tasking (user, Cycle 5):** "AI provenance is not good at all. What else? Keep pivoting until all personas agree."

**How this tasking is handled:**
- Personas are **simulated analytical perspectives, not interviewed experts**.
- Votes may not be raised to reach a threshold, and their agreement is not independent validation.
- Pivoting continues while evidence supports it. Each candidate is limited to five feedback iterations (doc 11).
- Section 9 states plainly what blocks consensus and which **real-world** evidence would unblock each holdout.
- No interviews were conducted. Measurements were taken in this repository on synthetic, benign data.

Labels: F = fact (sourced), I = inference, H = hypothesis. Grades A–D as in doc 02.

## Bottom line

1. **AI code provenance as a product is closed** after four cycles. A tool sold to labs has no buyer (I10). Provenance for IP code reuse is prior art and weak on real binaries (doc 14).
2. **The best pivot so far is N: binary-first malware-RE and threat-intel training environments and contamination-free evaluations, sold to frontier labs.**
   - It is the first candidate to score above the 3.5 BUILD line on the matrix: **3.70** (range 3.55–3.85).
   - The money comes from labs' post-training data budgets, which are far larger than Safeguards budgets (E68, E69).
   - The technical gap is documented by lab-affiliated researchers: frontier agents fully solve only about 27–32% of realistic RE instances in public settings (E72). Malware-analysis benchmarks show models "have not been trained to reason about cybersecurity analysis" (E74).
3. **Persona Round 5:** N has median 3.5 with **6/12** at ≥ 4. The bundle **Q (N plus the Cycle 4 Safeguards service M)** reaches **7/12**. This is the highest support in five cycles and still **no consensus** (gate ≥ 10/12).
4. **Decision: PIVOT to N, at PILOT FIRST, sold as Q.** BUILD is withheld because the consensus and buyer gates fail.
5. **Consensus cannot be reached with more desk pivots.** The remaining holdouts each need evidence only the real world can provide: a lab's dual-use review, counsel's export-control opinion, a paid pilot, and a human-validated hard task. One persona, the Supply-Chain Researcher, represents a different market and is structurally unlikely to rate any lab-focused product ≥ 4 (section 9).

## 1. Intelligence cycle (Cycle 5)

| Stage | What was done |
|---|---|
| Direction | Find where a malware-RE / threat-intel founder can sell to frontier labs (or adjacent AI-security buyers) with stronger evidence than M. New PIR-17–19. |
| Collection | RL-environment market reporting, cyber RL-environment vendors, RE and malware-analysis benchmarks, OpenAI's cyber programs, AI-agent-security acquisitions. One local build and measurement (X8). |
| Processing | E68–E78; inferences I15–I18 |
| Analysis | ACH (H14–H17), KAC (A37–A44), premortem (P28–P33), red team, persona Round 5, iterations 14–18, matrix N–Q, consensus-ceiling analysis |
| Dissemination | This document, plus updates to docs 01, 02, 05, 07, 11, 13 and EXECUTIVE_DECISION |
| Feedback | X9–X11 with pass/kill thresholds |

## 2. New PIRs

| PIR | Question | Answer | Confidence |
|---|---|---|---|
| PIR-17 | Which lab budget can a malware-RE founder access at scale? | Post-training data and RL environments. Anthropic reportedly discussed spending more than $1B over a year (E68); contracts are often six to seven figures per quarter (E69). Cyber is an active category with vendors selling to labs (E70). | Moderate (press and interview-based sources) |
| PIR-18 | Is binary-first malware RE under-supplied as training material? | Existing cyber environment vendors focus on source/web vulnerability find-exploit-fix (E70). Binary RE and malware sets are small evaluations: 12 cases (E73), 262 instances (E72). Training-scale supply was not found, but that is an absence of evidence. | Low–moderate |
| PIR-19 | Are adjacent AI-security tools (agent/MCP security, model scanning) better entries? | No. The segment consolidated into large platforms in 2025 (E77). | Moderate–high |

## 3. Evidence (E68–E78)

| ID | Evidence | Source | Grade | Type |
|---|---|---|---|---|
| E68 | Labs demand RL environments. Per The Information, Anthropic leaders discussed spending more than $1B over the next year. Surge reportedly had $1.2B revenue from labs and set up an environments organization. Mechanize works with Anthropic (two sources). | [TechCrunch](https://techcrunch.com/2025/09/21/silicon-valley-bets-big-on-environments-to-train-ai-agents/) | C | F |
| E69 | Epoch AI, from interviews: contracts often six to seven figures per quarter; $200–$2,000 per task is typical; RL use is 10–20× benchmark use; "substantially more in-housing" recently; vendors' value is that "they have the guys". | [Epoch AI](https://epoch.ai/gradient-updates/state-of-rl-envs) | C | F |
| E70 | Cyber RL-environment vendors selling to labs. Bugcrowd (May 2026): "already being used by leading LLM providers", with hundreds of thousands of environments built from OSS vulnerabilities. Symbiotic: 100+ vulnerability classes, difficulty bands calibrated on frontier models. TarantuLabs: generated exploit chains with deterministic verifiers. Starker: multi-host offensive networks. All focus on find/exploit/fix of source, web or network vulnerabilities. | [Bugcrowd](https://www.bugcrowd.com/press-release/bugcrowd-launches-reinforcement-learning-environments-to-help-ai-models-learn-real-world-security-skills/); [Symbiotic](https://symbioticsec.ai/solutions/industry/ai-labs); [TarantuLabs](https://tarantulabs.com/); [Starker](https://starker.ai/) | B (self-described) | F |
| E71 | Alice Labs Cyber RL benchmark: 12 tasks, including a malware-analysis gym with planted decoys. Some frontier models refuse pentest tasks at the API layer. | [Alice](https://alice.io/blog/cyber-rl-benchmark-v1-0-measuring-frontier-cybersecurity-capability) | C | F |
| E72 | SRE-Bench (authors from Columbia, UC Berkeley, Google DeepMind, OpenAI and Anthropic). 5,000+ expert hours; 19 private programs; 262 instances; 1,572 tasks. Over half of its 44 anti-analysis primitives have no public implementation. Public settings: GPT-5.6-Sol fully solves 31.5% and Claude-Fable-5.1 26.9%. Unconstrained: GPT-6-Astra reaches 88.0% pass@1 and 99.2% pass@4. Contamination control and realistic scale are both "essential". | [arXiv 2608.11469](https://arxiv.org/abs/2608.11469) | B (preprint) | F |
| E73 | MalwareBench (General Analysis): 12 obfuscated cross-platform cases with a 20-hour budget. The verifier checks findings and tests the model's config extractor on held-out variants and benign files. Human analysts score above 90% with a median of 12 hours. | [MalwareBench](https://malwarebench.com/blog/introducing-malwarebench) | B/C | F |
| E74 | CyberSOCEval (part of CyberSecEval 4): malware-analysis accuracy 23–34%. Reasoning models gain little, which suggests models "have not been trained to reason about cybersecurity analysis". | [arXiv 2509.20166](https://arxiv.org/abs/2509.20166) | B | F |
| E75 | OpenAI Daybreak (Trusted Access for Cyber) lists malware analysis and reverse engineering as authorized workflows, offers cyber-specialized models (e.g., GPT-5.6 Cyber), and committed $10M in API credits. | [Daybreak](https://help.openai.com/en/articles/20001258-openai-daybreak-trusted-access-for-cyber-overview); [Trusted Access](https://openai.com/index/trusted-access-for-cyber/) | B | F |
| E76 | OpenAI Aardvark, now Codex Security: an agentic security researcher productized for defenders | [OpenAI](https://openai.com/index/introducing-aardvark/) | B | F |
| E77 | AI-agent-security consolidation: Snyk acquired Invariant Labs (June 2025; MCP scanning, tool poisoning). Palo Alto Networks completed its Protect AI acquisition (July 2025; model scanning, red teaming, agent security). SentinelOne agreed to acquire Prompt Security (August 2025; MCP gateway covering 13,000+ servers). | [Snyk](https://snyk.io/news/snyk-acquires-invariant-labs-to-accelerate-agentic-ai-security-innovation/); [PANW](https://www.paloaltonetworks.com/company/press/2025/palo-alto-networks-completes-acquisition-of-protect-ai); [SentinelOne](https://www.sentinelone.com/press/sentinelone-to-acquire-prompt-security-to-advance-genai-security/) | B | F |
| E78 | **X8 measured here** (section 4) | `bench/results/re_tasks/results.json` | Measured (synthetic, benign) | F |

| ID | Inference | Basis | Confidence |
|---|---|---|---|
| I15 | Labs' largest outside spend in this space is on training data and environments, not Safeguards services. Cyber is an active category. | E68–E70, E75 | Moderate |
| I16 | Binary-first malware-RE material exists mostly as small evaluations. Training-scale supply looks thin. | E70, E72, E73 | Low–moderate (absence of evidence) |
| I17 | Fast saturation (E72, unconstrained 99.2% pass@4) means recurring demand for fresh, harder, contamination-free tasks, but per-task value decays quickly. | E72, E69 | Moderate |
| I18 | Agent/MCP security and model scanning have been absorbed by large platforms, which weakens a startup tool entry there. | E77 | Moderate–high |

**Contradictory evidence recorded:**
- In-housing is increasing (E69).
- Lab researchers co-authored SRE-Bench, so labs can source RE expertise from academia (E72).
- Generalist vendors (Surge, Mercor, Scale) have the expert pools and relationships (E68, E69).
- A malware-RE evaluation company already exists (E73).

## 4. Measurement this cycle (X8): verifiable malware-RE task generator

`re_tasks/` generates unique, benign "malware-like" binaries.
- Each carries a hidden configuration: a C2 host on the reserved `.test` TLD, campaign id, mutex, LLM endpoint and model, and an embedded key-shaped credential.
- Plaintext decoys are planted alongside it.
- Protection levels: L0 plaintext, L1 single-byte XOR, L2 LCG-keystream XOR.
- A deterministic verifier grades 7 fields. For the credential it asks only for the provider and last four characters, never the full value.
- The programs never open sockets, files or processes.

360 instances (3 levels × `-O0`/`-O2`/`-Os` × 40), all stripped:

| Level | Strings + `llm_indicators` | Single-byte XOR brute force | Family config extractor (analyst-level) |
|---|---|---|---|
| L0 plaintext | solved **19%**; fell for the decoy C2 67% | 100% | 100% |
| L1 single-byte XOR | 0%; fell for the decoy 100% | **78%** (mean field score 0.97) | 100% |
| L2 LCG keystream | 0% | **0%** | **100%** |

Uniqueness: 360/360 distinct binaries and 360/360 distinct C2 hosts.

What this shows:
- The pipeline works: unique instances, a deterministic grader, decoys that catch shortcut solvers, and a difficulty gradient.
- Every level is solvable without the answer key. The family extractor is what an analyst writes after reversing one sample, mirroring MalwareBench's held-out-variant extractor check (E73).

What it does **not** show:
- Market-grade difficulty. A frontier agent would likely solve L2 quickly; real value needs an expert-authored hard tier (E72: about 19 expert-hours per instance).
- That these tasks improve model skill (A40). That needs a training run we cannot do here.

## 5. Candidates

| ID | Offer | Buyer and budget |
|---|---|---|
| **N** | Binary-first malware-RE and threat-intel RL environments and contamination-free evaluations: a procedural generator for breadth, an expert-authored hard tier, deterministic verifiers, shortcut/decoy audits, and a benign-payload policy | Lab post-training and evaluation teams (data budget), directly or via data vendors |
| O | Malicious MCP-server / agent-skill supply-chain detection (RE of agent extensions) | Enterprises and AI platforms (security budget) |
| P | Malicious model-artifact scanning (pickle and similar payloads) | Model hubs, enterprises |
| **Q** | **N + M**: "the malware-RE partner for frontier labs", with environments for post-training and SME capacity for Safeguards | Two budgets inside the same lab |

## 6. ACH: which route sells this founder's skills to labs?

- H14: Labs will buy malware-RE environments/evals directly from a specialist.
- H15: Labs will buy them only through generalist data vendors, so the specialist works as a subcontractor.
- H16: Labs will build cyber environments in-house; no outside purchase.
- H17: Agent-security or model-scanning tools are a better entry.

| Evidence | H14 | H15 | H16 | H17 |
|---|---|---|---|---|
| E68 environment spend | C | C | **I** | N |
| E69 in-housing trend | **I** | N | C | N |
| E69 vendors "have the guys" | N | C | **I** | N |
| E70 specialist cyber vendors sell to labs | C | **I** | **I** | N |
| E72 5,000 expert hours; RE is a frontier | C | C | N | N |
| E72 lab researchers co-author with academia | N | N | C | N |
| E73 a malware-RE eval startup exists | C (category) / competitor | N | N | N |
| E74 models untrained for cyber analysis | C | C | N | N |
| E75 malware analysis is a sanctioned defensive workflow | C | N | N | N |
| E77 consolidation | N | N | N | **I** |
| **Inconsistencies** | **1** | **1** | **3** | **1** (no consistent evidence) |

Reading: H14 and H15 are both well supported, so pursue direct sales **and** data-vendor channels. H16 is the least consistent. H17 has no positive evidence.

## 7. KAC and premortem

| ID | Assumption | Status |
|---|---|---|
| A37 | Labs want binary-first malware-RE *training* tasks, not only evaluations | Plausible (E74, E72); untested directly |
| A38 | A small specialist can meet lab QA bars | **Untested** (X9, X10) |
| A39 | Expert task cost is below price | **H.** SRE-Bench is about 19 expert-hours per instance with 6 tasks each (E72), against $200–$2,000 per task (E69). Viable only if expert rates and authoring tooling keep per-task cost within that range. |
| A40 | Benign-payload tasks transfer to real malware-analysis skill | **Untested** |
| A41 | The dual-use and export-control posture is acceptable (benign payloads, private delivery, no publication of novel evasion primitives) | **Untested; counsel needed** (X11). Not rated a critical blocker because a conservative mode exists. |
| A42 | Procedural generation gives non-memorizable diversity | Partly supported (X8: 360/360 unique); toy difficulty only |
| A43 | The founder can recruit and QA a small RE expert network | **Untested** |
| A44 | Labs buy direct from small cyber specialists | Plausible (E70); unverified for small firms |

| ID | Failure story | L | S | D | RPN |
|---|---|---|---|---|---|
| P28 | Surge, Mercor, Scale or Bugcrowd add malware-RE environments with bigger expert pools | 4 | 4 | 3 | 48 |
| P30 | Saturation treadmill: per-task value collapses faster than authoring cost falls | 4 | 3 | 3 | 36 |
| P31 | Shortcut or reward-hacking flaws found by a lab, rejecting the batch | 3 | 4 | 2 | **48** |
| P29 | Labs build in-house | 3 | 5 | 3 | 45 |
| P33 | RE expert recruitment does not scale | 3 | 4 | 3 | 36 |
| P32 | A novel anti-analysis primitive leaks and helps attackers | 2 | 5 | 4 | 20 |

Mitigations:
- P31: shortcut baselines and decoys on every batch (X8 pattern), and held-out-variant extractors.
- P32: benign payloads, private delivery, no publication.
- P28: subcontract to those vendors instead of competing (H15).

## 8. Red team

| View | Attack | Response |
|---|---|---|
| Lab post-training lead | "Surge already staffs our cyber tasks." | Then sell through Surge (H15). The specialist edge is RE QA and hard-tier authoring. |
| Lab safety reviewer | "Training on anti-analysis makes models better at writing evasive malware." | A real dual-use concern. Labs already sanction RE and malware analysis (E75). Tasks target *analysis*, not authoring; no novel evasion is published. Needs the lab's own review (X10). |
| Competitor (MalwareBench/General Analysis) | Already has frontier-calibrated malware cases | Differentiate on training scale (generator), threat-intel attribution tasks (Cycle 4 indicators), and Safeguards integration (Q). |
| Threat actor | — | Not applicable directly; P32 covers leakage. |
| Skeptical VC | "Data-services margins; a treadmill." | Accepted (P30). Venture scale is unproven; Mechanize, Irregular and Mercor show the category can raise money (E60, E61, E68). |

## 9. Persona Round 5 (simulated)

Dimensions: Importance, Technical, Demand, Defensibility, Privacy/legal, Founder fit, Adoption, **Overall**.

### N: malware-RE environments and evaluations for labs

| # | Persona | Imp | Tech | Dem | Def | Priv | Fdr | Adopt | **Ovr** | Justification |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Abuse Investigator | 3 | 4 | 4 | 3 | 3 | 4 | 3 | **3** | Improves defenders' models, but not their enforcement workflow |
| 2 | T&S Eng Lead | 3 | 4 | 4 | 2 | 3 | 4 | 3 | **3** | Dual-use review outstanding (A41) |
| 3 | Infra Architect | 3 | 4 | 4 | 3 | 4 | 4 | 4 | **4** | Clean deliverable (sandbox + verifier); no data custody |
| 4 | Malware RE | 4 | 4 | 4 | 3 | 3 | 5 | 4 | **4** | Core skill; contamination-free expert tasks are scarce (E72) |
| 5 | ML Scientist | 4 | 4 | 4 | 3 | 3 | 4 | 4 | **4** | Verifiable rewards, decoys, difficulty gradient measured (X8); transfer untested (A40) |
| 6 | Supply-Chain Researcher | 2 | 4 | 3 | 2 | 3 | 3 | 3 | **3** | Outside this persona's market |
| 7 | Detection Eng Lead | 4 | 4 | 4 | 3 | 3 | 4 | 4 | **4** | Config-extractor tasks equal detection-engineering skill |
| 8 | Forensics Investigator | 3 | 4 | 4 | 3 | 3 | 4 | 4 | **4** | Deterministic grading; authoring provenance is auditable |
| 9 | Privacy Counsel | 3 | 4 | 3 | 3 | 3 | 3 | 3 | **3** | Export-control and dual-use opinion needed (A41); no personal data |
| 10 | AI Security CISO | 4 | 4 | 4 | 2 | 3 | 4 | 3 | **3** | Important (E75), crowded vendor field (E70) |
| 11 | Procurement/GTM | 3 | 4 | 4 | 3 | 3 | 4 | 4 | **4** | Known budget, contract sizes and channels (E68–E70) |
| 12 | Skeptical VC | 3 | 4 | 4 | 2 | 3 | 4 | 3 | **3** | Services margins, saturation treadmill (P30) |
| | **Median** | 3 | 4 | 4 | 3 | 3 | 4 | 3.5 | **3.5** | |

Overall ≥ 4: **6/12** (Infra, RE, ML, Detection, Forensics, GTM).

### Q: N + M bundle

Changes from N, each with its reason:
- Abuse Investigator Imp 3→4, Ovr 3→4: adds direct enforcement capacity (Cycle 4 I12).
- CISO Ovr stays 3: vendor sprawl, though misuse and defence are covered.
- VC Ovr stays 3: two motions dilute focus.

All other votes are as for N. **Q: 7/12 at ≥ 4, median 4.**

| Gate (Q) | Result |
|---|---|
| ≥ 10/12 overall ≥ 4 | **Fail (7/12)** |
| No unresolved critical legal blocker | Pass (A41 open but not critical; conservative mode exists) |
| CISO and Abuse Investigator importance ≥ 4 | **Pass** (4, 4) |
| Credible validation path | Pass (X8 measured; X9–X11 defined) |
| ML + RE agree validation is valid | Pass for the pipeline; transfer (A40) is untested |
| Procurement identifies buyer and process | **Pass** on paper (post-training budget, data-vendor channel); no named buyer |

Other candidates: O agent/MCP supply chain, median 2.5, 1/12 (Supply-Chain Researcher). P model scanning, median 2, 0/12.

**No votes were adjusted.**

### Consensus ceiling: what would move each holdout on Q

| Persona (Ovr) | Evidence that would justify ≥ 4 | Obtainable by desk research? |
|---|---|---|
| T&S Eng Lead (3) | A lab's safety team approves the benign-payload and analysis-only policy | No (X10) |
| Supply-Chain Researcher (3) | A supply-chain variant (malicious package/agent-skill RE tasks) bought by a lab | No; and this persona's market is structurally different |
| Privacy Counsel (3) | Written export-control and dual-use opinion (X11) | No |
| AI Security CISO (3) | A lab confirms it would buy outside cyber environments rather than build them | No (X10) |
| Skeptical VC (3) | A paid pilot at the reported contract scale, or LOIs from two labs | No (X10) |

The maximum supportable today is **7/12**. Reaching 10/12 requires X9–X11 results. Unanimous 12/12 may never be reachable, because the Supply-Chain persona deliberately represents a different market. The agreed bar (≥ 10/12) is therefore the right target, not unanimity.

## 10. Feedback loop (iterations 14–18, candidate N)

N used all five allowed iterations. Further objections can only be resolved by X9–X11.

| It. | Objection (persona) | Type | Test | Evidence | Result | Change |
|---|---|---|---|---|---|---|
| 14 | "Crowded: Bugcrowd, Symbiotic, TarantuLabs, Starker, Alice, MalwareBench, Surge/Mercor" (VC, GTM) | Competitive | Do current vendors cover binary-first malware RE at training scale? | E70–E73 | Partly refuted: vendors cover source/web/network vulnerabilities; malware-RE sets are small evaluations | Position as binary-first malware RE + threat-intel tasks at training scale; subcontract via data vendors |
| 15 | "Saturates fast" (ML) | Technical / business | How fast do frontier agents saturate realistic RE? | E72 (99.2% pass@4 unconstrained) | Supported | Recurring-refresh model: generator for breadth, expert hard tier, difficulty recalibrated per model release |
| 16 | "Dual-use: teaches evasion" (T&S, Privacy) | Ethical / legal | Do labs sanction malware analysis and RE as defensive? | E75 | Mitigated, not closed | Benign-payload, analysis-only, private delivery, no publication of novel primitives; counsel (X11) |
| 17 | "Labs in-house it" (Infra, VC) | Business | Do vendors still win despite in-housing? | E69, E70 | Yes, for expert supply ("they have the guys") | Sell expert supply and QA, not a platform |
| 18 | "Can a generator make verifiable, non-shortcuttable RE tasks?" (ML, RE) | Technical | X8: unique instances, gradient, decoys, solvable without the key | E78 | **Passed** at toy difficulty | Hard tier must be expert-authored; transfer still untested (A40) |

## 11. Weighted decision matrix (weights as in doc 11)

| Criterion (weight) | **N** RE environments | O Agent/MCP supply chain | P Model scanning | **Q** N + M |
|---|---|---|---|---|
| Unmet need (20%) | 4 (E72, E74) | 4 | 3 | 4 |
| Technical feasibility (15%) | 4 (X8; E72 shows expert cost) | 3 | 4 | 4 |
| Differentiation (15%) | 3 (binary-first malware RE; E70 gap) | 1 (E77) | 1 (E77) | 3 |
| Founder advantage (10%) | 5 (RE) | 4 | 3 | 5 |
| Customer accessibility (15%) | 3 (direct + vendor channel) | 2 | 2 | 3 |
| Willingness to pay (15%) | 4 (category spend: E68–E70) | 3 | 3 | 4 |
| Regulatory/privacy (10%) | 3 (A41) | 4 | 4 | 3 |
| **Weighted** | **3.70** (3.55–3.85 for differentiation or access ±1) | 2.95 | 2.80 | **3.70** |

History of the best candidate per cycle: original concept 1.95 → F 2.94 → F 2.65 → M 3.45 → **N/Q 3.70**.

## 12. Decision

**PIVOT to N, sold as Q, at PILOT FIRST.**
- N/Q is the first configuration above the 3.5 score line.
- BUILD is withheld because the consensus gate (7/12) fails and there is no named buyer.
- The engineering already allowed is the generator, grader and audits. A hard tier is built only for X9.
- M (Cycle 4) becomes Q's Safeguards add-on. F stays at RESEARCH FIRST as the fallback.

| Experiment | Pass | Kill |
|---|---|---|
| **X9 Hard-tier pilot.** 5 expert-authored benign tasks with realistic anti-analysis. Run a local open-weight agent baseline (no external AI services), record human-analyst solve times, and run shortcut audits. | ≥ 3/5 unsolved by the local baseline but solved by a human within budget; no shortcut found | Tasks are shortcuttable or unsolvable by humans |
| **X10 Buyer discovery.** 10 conversations with lab post-training/cyber-eval and Safeguards staff, plus 3 data vendors (subcontract channel). Non-leading questions as in doc 15 §14, adapted to environments. | ≥ 2 request sample tasks under NDA **and** ≥ 1 paid batch or subcontract | < 1 sample request, and vendors decline |
| **X11 Counsel.** Dual-use and export-control review of the benign-payload policy; contract IP for task ownership. | Written policy approved | Delivery requires controls that make the work infeasible |

If X10 fails: fall back to M (lab Safeguards services) if X5/X6 pass. Otherwise F at RESEARCH FIRST, and then STOP.

## 13. Constraint compliance

- No fabricated interviews, votes, sources or results. X8 numbers are from `bench/results/re_tasks/results.json`.
- Generated binaries are benign: no network, file or process activity. Hosts are `.test`; key-shaped strings are random and created at runtime. The answer key holds only the last four characters of a credential.
- No real malware was used. Nothing was sent to external AI services. The founder's classifier was not present, used, or retrained.
