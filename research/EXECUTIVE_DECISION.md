# EXECUTIVE DECISION

## Decision: **PIVOT**. Do malware-RE expert work now as income (AB), and take adversarial-robustness testing of AI malware-analysis pipelines (AD) to **PILOT FIRST**

**Cycle 8 (doc 19): Z is already offered by others** (doc 18 §15):
- malware-RE capability evaluations: General Analysis MalwareBench, Irregular, Dreadnode, the AISIs;
- uplift adjudication: Anthropic's CJS scale with HackerOne, and the FMF framework.

Ten more ideas were screened against live competitor searches (doc 19 §3).

| Option | Status |
|---|---|
| **AD: adversarial-robustness testing of AI malware-analysis pipelines.** A corpus of AI-analysis-evasion text plus a verdict-flip harness, sold as fixed-price test sprints and regression suites to vendors whose triage uses LLMs. Labs come in only as a secondary buyer, because their models act as the analysts. | **PILOT FIRST.** Weighted 3.45, the best idea that is a company. Round 8: 7/12. **No consensus.** |
| **AB: malware-RE expert work through AI-training marketplaces and evaluators** | **Do now as income** (3.70, but a job, not a company) |
| Z (Cycle 7) | Downgraded: differentiation 3 → 1 (3.70 new weights); its vote is superseded |
| AE public comparative tests | First fallback; then M; then STOP |
| AC, AF, AG, AH, AI, AK | Crowded, free, or credential-gated (doc 19 §3) |
| AJ | Knocked out by G-solo (24/7 incident response) |

### Cycle 8 in brief

- **Need (facts):**
  - Malware already embeds text aimed at AI triage: Talos A3 (84 samples in 4 families), SentinelOne's Gaslight, and ESET's GuardBreaker (E101–E103).
  - ALIBI's cover stories flip 30/35 malicious verdicts on Gemini 2.5 Pro and cause large downgrades on GPT-5.5 Pro and Claude Opus 4.7. Deployed products were never tested (E104).
- **Competition:**
  - Generic AI red-teamers (HackerOne, IronSOC, Arcanum) test prompt injection in general (E107).
  - No specialist in robustness testing of AI malware analysis was found. That is absence of evidence, so low confidence (I28).
  - AV-Comparatives or SE Labs could enter quickly (P45).
- **Built and measured (`re_tasks/injection.py`, E117):** a static detector for evasion text, the defence Talos recommends.
  - It catches 83% of plain ASCII payloads.
  - It catches **0/30 cover stories, 0/42 spaced-letter payloads and 2/42 homoglyph payloads**.
  - False positives: 2/5,000 real benign files (10 before a line-splitting fix).
  - No LLM was run, so flip rates are not reported.
- **Next:**
  - X22: run flip rates on 3 local open-weight models.
  - X23: five vendor sprint offers; zero paid or LOI means fall back.
- **Goal drift:** AD sells mainly to security vendors. The frontier-lab angle survives only as an evaluation add-on.

### Cycle 7 result (Z, now downgraded)


**Cycle 7 (doc 18): the founder rejected W's post-deployment half as unrealistic.** Monitoring stolen keys and access markets is deep- and dark-web (DDW) collection (KELA's and Flashpoint's business), and the incident bridge needs incident-response firms to supply cases (E96). A new knockout gate requires that the founder plus at most two contractors can deliver the offer without a collection or supply network. What survives is the one lab-proof moat that needs no network: **independence**.

| Option | Status |
|---|---|
| **Z: independent malware-capability evaluator.** (1) Capability evaluations: can a model analyse and build malware-grade components, scored on a private, canary-stamped, deterministically graded task bank. (2) Uplift adjudication: expert RE judgement of whether red-team or bounty outputs are *working* malware "beyond … publicly available tools" (E92). Sold to labs under EU Code App. 3.5, the AI Office's Network of Evaluators, AISIs, and bounty or arena platforms. | **PILOT FIRST.** Weighted **3.70** (old) / **3.90** (new), the best among feasible candidates. Persona Round 7: **8/12** at ≥ 4. **No consensus**; BUILD withheld. |
| W (Cycle 6) | **Withdrawn** (E96). Its 3.85 / 4.00 and 9/12 assumed networks the founder lacks. `incident_packet` is kept as reference code. |
| N/Q (Cycle 5) | Not sold to any lab Z evaluates (financial-influence conflict, E90) |
| M (Cycle 4) | First fallback; F second; then STOP |

### Cycle 7 in brief

- **Why labs can't do it themselves:** the AI Office (Oct 2026) requires evaluators to be "free from the provider's managerial, financial or operational influence" (E90). That rules out in-house work and captive spin-outs.
- **Why the founder can do it alone:** it needs RE skill, a task bank (`re_tasks`, built) and conflict-free revenue. It does not need sources, personas or victim data. There is an entry route: the AI Office recruits evaluators through public calls into a Network of Evaluators, selecting on evaluation track record (E91).
- **Niche against incumbents:** public safeguard tests mostly score text for "usable operational details" (E93), while the bounty bar is *working* malware beyond public tools (E92). Irregular covers network and exploitation evaluations (E87). Whether anyone pays for outside adjudication is untested (A55, X19).
- **Built and measured (X20):** `re_tasks/evaluate.py` adds Wilson 95% intervals, a significance gate, per-bank canaries and disjoint per-customer partitions.
  - 180/180 tasks were canary-stamped and none of 540 solver outputs contained the canary; partitions were disjoint.
  - **Per-customer privacy costs power:** with about 20 tasks per level per lab, 100% vs 90% is not distinguishable (p = 0.15), and a perfect 17/17 only supports ≥ 82%. Expert time must go into task families, with generated instances.
- **Why no consensus (8/12):**
  - Abuse Investigator: Z no longer touches enforcement.
  - Privacy Counsel: needs a dual-use and export-control opinion (X11).
  - Skeptical VC: needs a paid pilot (X19).
  - Supply-Chain Researcher: represents a different market.
- **Next:**
  - X17: three expert task families, evaluated on local open-weight models, with the methods published.
  - X18: apply to the AI Office's evaluator network, one lab's published criteria, and UK AISI.
  - X19: an uplift-adjudication pilot.
  - X11: counsel.

### Cycle 6 result (W, now withdrawn)

**Cycle 6 (doc 17) added the criterion "a frontier lab must have trouble replicating it."** Everything offered to labs in Cycles 1–5 failed that test. Tools, data, RE talent and evaluation content can all be hired, built or bought. Labs already do provenance in-house (E55, E57), in-house environments (E69), and co-author RE benchmarks (E72).

| Option | Status |
|---|---|
| **W: independent cyber-misuse assurance for frontier labs.** After deployment (V): monitor malware, stolen keys and LLM mixers across providers, and turn victim-consented incident evidence into provider-neutral packets shaped for EU Code Measure 9.2. Before deployment (R): independent malware-RE evaluations from a private task bank. | **PILOT FIRST.** Weighted **3.85** (old weights) / **4.00** (with a 15% lab-replication criterion), the highest in six cycles. Persona Round 6: **9/12** at ≥ 4. **No consensus**; BUILD withheld. |
| Q = N + M (Cycle 5) | **Fallback.** Lab replication difficulty 2, so it drops to 3.45 under the new weights. N's task bank becomes W's pre-deployment component. |
| F: IP code-reuse investigation | RESEARCH FIRST, second fallback |

### Cycle 6 in brief

- **What a lab cannot replicate** (I19):
  - **Independence from itself.** EU GPAI Code Appendix 3.5 requires independent external evaluators and bars training on their test runs (E79). SB 53 requires disclosing third-party assessment (E83).
  - **Victim-side presence.** Responders see the victim network; the lab sees only its platform (E84, E57).
  - **Neutrality across competitors.** Stolen keys are resold across 30+ providers through "LLM mixers" (E85).
  - **Activities labs avoid**, such as handling victim incident evidence.
- **The regulatory slot is written down.**
  - Measure 3.5 lists "monitoring … known malware, public forums" and "provenance techniques" as post-deployment monitoring methods, and grants independent evaluators access for that monitoring (E80).
  - Measure 9.2 incident reports need "material … setting out the model's involvement" (E81).
  - OpenAI, Anthropic, Google, Microsoft, Amazon and Mistral signed the full Code; xAI signed the Safety and Security chapter (E82).
- **Built and measured:** `provenance/incident_packet.py` builds consent-gated, provider-neutral packets. On 200 synthetic incidents (E89):
  - 0 cross-provider leaks and 100% routing of indicators to the right provider;
  - 0 leaks of credentials, IPs, emails, internal hosts, accounts and user paths;
  - **unlisted personal names leak 400/400 and victim-owned external hosts leak 200/200**. These require a victim-supplied term list and human review;
  - the first run leaked IPv6 200/200, which is now fixed.
- **Honest limit:** W is hard for labs to replicate, not for incumbents. Google (lab + Mandiant + VirusTotal), Unit 42 and TI vendors each hold part of it (P34, P37). Pseudonymised packets are still personal data (E88).
- **Why no consensus (9/12):**
  - Privacy Counsel needs a written DPIA and lawful-basis opinion (X16).
  - Skeptical VC needs a paid pilot or LOI from a non-Google signatory (X15).
  - Supply-Chain Researcher represents a different market.
- **Next:**
  - X13: the evaluator route via signatories' Appendix 3.5 criteria and public calls.
  - X14: 5 IR firms or insurers for edge-mode packet building on consented cases.
  - X15: 8 non-Google signatory conversations.
  - X16: counsel.
  
  Then persona Round 7 (doc 13, Cycle 6 track).

### Cycle 5 result (now the fallback, and W's task-bank component)

**Cycle 5 (doc 16) kept pivoting toward persona consensus.** The result:

| Option | Status |
|---|---|
| Original concept: an attribution *platform/tool* sold to AI providers | **STOP.** Labs already do artifact↔generation checks in-house (E55, E57). No buyer signal for a tool. |
| **Q = N + M: the malware-RE partner for frontier labs.** N: binary-first malware-RE and threat-intel RL environments and contamination-free evaluations (lab post-training budget). M: Safeguards SME services. | **PILOT FIRST.** Weighted **3.70** (range 3.55–3.85), the first candidate above the 3.5 line. Persona Round 5: **7/12** at ≥ 4 (N alone 6/12). **No consensus**; BUILD withheld. |
| M alone (Cycle 4) | Folded into Q as its Safeguards add-on (3.45; 3/12) |
| F: IP code-reuse investigation | **RESEARCH FIRST** fallback (sections 1–12 below, unchanged from Cycle 3) |
| O agent/MCP supply-chain security; P model scanning | **Not pursued.** Consolidated into large platforms (E77); 2.95 and 2.80 |

### Cycle 5 in brief

- **Why N:**
  - Labs' biggest outside spend is training data and RL environments. Anthropic reportedly discussed more than $1B over a year, and contracts are often six to seven figures per quarter (E68, E69). Cyber environment vendors already sell to labs (E70).
  - Those vendors focus on source/web vulnerabilities. Binary-first malware RE exists mainly as small evaluations (E72, E73).
  - Frontier agents fully solve only 27–32% of realistic RE instances in public settings (E72). Malware-analysis benchmarks show models are untrained for it (E74).
  - Labs sanction malware analysis as a defensive workflow (E75).
- **Built and measured:** `re_tasks/` generates unique, benign malware-like binaries with hidden configurations and decoys, plus a deterministic grader. Across 360 instances (E78):
  - strings-only solves 19% at L0, where it falls for the decoy 67% of the time;
  - single-byte XOR brute force solves 78% at L1;
  - only an analyst-style family extractor solves L2 (100%).
  
  This is toy difficulty; the real value is an expert-authored hard tier.
- **Why no consensus:** the five holdouts (T&S, Supply-Chain, Privacy Counsel, CISO, VC) need real-world evidence:
  - a lab dual-use review;
  - an export-control opinion;
  - confirmation that a lab buys rather than builds;
  - a paid pilot.
  
  Desk research cannot supply these. Unanimity may never be reachable, because the Supply-Chain persona represents a different market; the agreed bar is ≥ 10/12.
- **Next:** X9 hard-tier pilot, X10 buyer discovery with lab teams and data vendors, X11 counsel (doc 13, Cycle 5 track). Then persona Round 6.

### Cycle 4 result (now folded into Q)

| Option | Status |
|---|---|
| **M: SME-led AI-misuse malware intelligence and enforcement support for labs** | PILOT FIRST in Cycle 4. Weighted 3.45 (range 3.30–3.60), below the 3.5 BUILD line. Persona median 3, 3/12 at ≥ 4. **No consensus.** |

### Cycle 4 in brief

- **Problem labs have:** malware now calls LLM APIs at runtime and often embeds provider keys. Google GTIG reports PROMPTFLUX and PROMPTSTEAL/LAMEHUG (E51, E52), and SentinelOne's retrohunt found almost 8,000 key-bearing samples in a year (E54). Labs must answer "was this ours, and which account?", and published reports are criticized for missing verifiable indicators (E56).
- **Who does it today:** the labs, in-house. Anthropic saw malware on VirusTotal "within 2 hours of Claude generating the code" (E55). OpenAI checked whether the Trellix-reported binaries came from its models (E57).
- **What labs buy from outside:** expert capacity, not attribution tools.
  - Anthropic's cyber-harms enforcement team includes "contractors" (E58).
  - OpenAI uses SME probing (E59).
  - Irregular (E60) and Mercor (E61) earn revenue from labs.
  - Evidence of WTP for *this* work is indirect.
- **The offer (hypotheses):**
  1. Free door-opener: provider-verifiable disclosure packets for key-bearing malware found in public sources. The packet holds sha256 + offset + redacted key and is never tested.
  2. Paid core: surge malware-RE and enforcement-investigation capacity under the lab's data custody.
  3. Later: generation↔artifact tooling deployed inside the lab.
- **Built and measured this cycle:** `provenance/llm_indicators.py`.
  - Credential recall 1.0 on plain, UTF-16, Python and VBScript samples.
  - Recall 0.0 on split, XOR and base64 keys (these need RE).
  - 0/5,000 benign system files flagged.
  - Endpoint, model and prompt strings fire on 11/11 benign LLM SDKs, so they are triage hints, never evidence of malice (E66, E67).
- **Biggest risks:**
  - Labs cover it in-house plus FMF sharing (P21, RPN 60).
  - Vendors give the intel away free (P22).
  - The work is commoditized as hourly labour (P23).
  - Malware shifts to local models or stolen keys (P26). A stolen key points to a **victim**.
- **Next:**
  - X5: 60-day public-data hunting pilot with human RE and responsible disclosure.
  - X6: 10 lab Safeguards/Threat Intel conversations (doc 15 §14).
  - X7: model-attribution lead benchmark.
  - Counsel review of the disclosure protocol.
  - **If X5 and X6 both fail, labs are not viable for this offer.** F stays at RESEARCH FIRST and the default is STOP.

---

## Fallback track: IP code-reuse investigation (F) — Cycle 2–3 analysis

The original concept, an AI Code Provenance and Malware-to-Generation Attribution platform sold to AI providers, is **not** a viable standalone business on current evidence.

The earlier pivot target is **IP code-reuse investigation**: detecting a company's proprietary code inside third-parties' compiled products. This target is at **RESEARCH FIRST** status (downgraded from PILOT FIRST after the Cycle 3 peer-reviewed literature review, doc 14). **No platform build is authorized** until the three experiments below pass their gates.

> **Cycle 3 update (real research papers, doc 14).** The literature confirms the direction but sharpens three problems:
> - **Our matching method is prior art.** B2SFinder (ASE 2019) is near-identical.
> - **Similarity-scoring tools reach only about 20–60% recall on real binaries** (FSE 2026; ISSTA 2026). That contradicts our synthetic 100%.
> - **EU law permits decompilation only for interoperability.**
>
> It also shows a working path: retrieve, then verify with evidence. That approach reaches 93.7% recall and 97.6% precision on real stripped binaries, and about 91–92% with a local open-weight model.

> **Evidence basis.** All persona votes are *simulated analytical perspectives*, not interviews; their agreement is not independent validation. **No customer interviews were conducted.** All benchmark numbers come from a **synthetic benign C corpus** built and measured in this repository. The founder's malware classifier and datasets were **not present** in the repository (E01), so they were not validated, used, or modified.

---

### 1. Recommended product
**An owner-custodied proprietary-code fingerprinting service with binary/firmware matching and evidence-grade reports.**

- The IP owner fingerprints its own source on its own premises with a secret key.
- Suspect third-party binaries, firmware, or packages that were lawfully acquired are matched against the keyed index.
- Matches above a calibrated open-set threshold produce a reproducible **evidence packet**: matched features, locations, alternative explanations, and limitations.
- A human software-forensics expert reviews every packet.

The original binary→source engine is reused as the *retrieval* stage (doc 12). Peer-reviewed results require a **local evidence-verification stage** after it, and **filtration** of unprotectable or OSS features so reports align with the abstraction–filtration–comparison test (E36, E50a). Stylometry is excluded from evidence because it can be forged (E45).

### 2. Target customer
Hypotheses, to be tested in X2:
- **Primary:** IP litigation counsel and software-forensics expert firms, buying per matter.
- **Secondary:** in-house IP counsel at embedded/OEM, gaming, security-software, and semiconductor companies; M&A technical-diligence providers.

AI providers are **not** the target *for F or for a tool*. Buyers are few, they build in-house, and session data cannot leave them (doc 11, iteration 1). Cycle 4 sells *services* to them instead (M, top of this document).

### 3. Exact problem
An IP owner suspects that its code (via a departing employee, a contractor, a leak, or AI-memorized snippets) is shipping inside a competitor's or supplier's compiled product. Today, finding out requires:
- **source-only** leak monitors, which cannot see compiled products (E26); or
- expensive expert work, usually only **after** litigation discovery (E21, E22).

The owner lacks a cheap, private, pre-filing way to triage which third-party artifacts likely contain its code.

### 4. Evidence of demand
**Indirect only; direct demand is UNKNOWN.**

| Evidence | What it shows |
|---|---|
| *Motorola v. Hytera*: code copied into firmware with renamed functions; $764.6M verdict (E22) | Real loss from copied code in compiled products |
| More than 1,500 federal trade-secret filings in 2025, a record (E23) | Litigation volume |
| CodeSuite exists as a commercial expert tool (E21) | Some spend exists on software forensics |
| Source-leak monitoring products exist (E26) | Owners pay to protect source code |

None of these shows that anyone will pay for *this* product. Willingness to pay is scored UNKNOWN in the decision matrix (doc 11).

### 5. Differentiation
**Low confidence (lowered in Cycle 3).** Algorithmic novelty is ruled out: B2SFinder (E32), BAT (E29), and winnowing/MOSS (E43). Commercial binary→source products exist for OSS: BinaryAI SaaS (E33), a BLADE-based commercial deployment (E36), and Black Duck, Scantist, and Cybellum (E37). Any remaining differentiation is the **proprietary-code infringement evidence workflow** (filtration, custody, reproducible exhibits, expert review), and it is unproven.

What is not novel:
- String and constant binary→source matching is established prior art (BAT/BANG, E29).

What we have not found elsewhere (I07, weakened in Cycle 3), though it may exist unpublicized:
- combining keyed, owner-held fingerprints, so the vendor never sees plaintext code;
- open-set calibrated escalation;
- packaging binary matches as *infringement* evidence: filtration-ready, reproducible, expert-reviewed.

Coverage of compiled artifacts on its own is **not** a differentiator. Binary SCA vendors already do it for OSS (E33, E36, E37). Incumbents (Cycode, BigID, SAFE, Black Duck, BinaryAI) could add proprietary-corpus indexing (A19 fails, P11, P19).

### 6. Technical feasibility
**Feasible for non-evasive reuse on synthetic data; weak against deliberate obfuscation; unproven on real code. Peer-reviewed real-world studies indicate that scoring-only matching is insufficient (E35, E36).** Measured on synthetic data with a 10k-record index (E30):

| Condition | Default corpus | Boilerplate-heavy corpus |
|---|---|---|
| gcc -O3 stripped, R@10 | 1.000 | 0.912 |
| Function transplant into a new host, R@10 | 1.000 (R@1 0.845) | 0.66 |
| String obfuscation + constant mutation, R@10 | 0.768 | 0.348 |
| False escalations on 400 held-out out-of-index binaries | 0 | 0 |
| Opcode-n-gram baseline at O2, R@10 | 0.034 | — |

- The provisional targets (R@10 ≥ 90%, false-escalation rate ≤ 1%, latency < 10 s) are met for naive builds and **not met** for adversarial or boilerplate-heavy conditions (doc 09).
- Cost is about 1.5 KB per record and 0.28 ms median search.
- Real-code validity is the gating unknown (X1). **Peer-reviewed real-world evidence is unfavourable for scoring-only designs:**
  - average recall < 60% and precision ≈ 75% across 11 tools (E35);
  - B2SFinder, closest to our design, at 19.9% recall and 47.9% precision (E36);
  - domain-specific code < 45% (E37).
- It is favourable for retrieve-then-verify: 93.7% / 97.6% (E36).
- Our 0/400 false-escalation result should be treated as a synthetic upper bound.

### 7. Reusable founder assets

| Asset | Status |
|---|---|
| Malware ML classifier | **Not found in the repository.** Not used, not retrained, not overwritten. An adapter interface exists (`provenance/classifier.py`). Its output is treated as model opinion only. |
| Malware/benign datasets | **Not found.** Validation protocols (license, provenance, leakage, label quality) are in doc 08. |
| Reverse-engineering expertise | The strongest relevant asset: the simulated RE and forensics personas rate founder fit 5 and 4 for F. Unverified. |
| Threat-intel network | Fits AI-provider and security buyers. It does **not** obviously reach legal buyers (A24, untested). |

### 8. Top 5 existential risks
1. **Real binaries defeat feature matching.** Peer-reviewed tools reach about 20–60% recall on real binaries (P18; E35, E36). Our synthetic results overstate recall (P3; boilerplate-heavy IP recall is already 0.66). Deliberate obfuscation makes this worse (P2, E30b).
2. **Incumbents or deployed binary SCA vendors add "index your own code"** (P19, RPN 64, the highest after Cycle 3; P11; A19 fails; E33, E36, E37).
3. **Lawful acquisition and analysis of third-party binaries is restricted.** EU decompilation is interoperability-only, and the US position is fact-specific (A16; critical blocker; E50).
4. **No recurring demand.** IP buyers prefer hourly experts, leaving a services business (P9).
5. **Evidence is challenged in court.** Matches on unprotectable or OSS elements are filtered under abstraction–filtration–comparison (E50a), and expert alternative explanations apply (E21). Weak filtration would turn hits into non-evidence.

For the original concept, the dominant risks were providers building in-house (P1), adversary obfuscation (P2), and session-data custody (P5). These led to its rejection.

### 9. Persona votes (simulated)
Overall attractiveness is scored 1–5 by 12 personas (doc 07). Medians of the overall-attractiveness scores:

| Configuration | Median | Personas voting ≥ 4 |
|---|---|---|
| Original concept | 2 | 0 / 12 |
| A Provider SDK | 2 | 0 / 12 |
| B Binary→source platform | 2 | 0 / 12 |
| C Supply-chain provenance intel | 2 | 0 / 12 |
| D Coding-agent observability | 2 | 0 / 12 |
| E Hybrid malware intel + provenance | 2 | 0 / 12 |
| F IP code reuse (Round 2) | 3 | 2 / 12 (RE, Forensics) |
| **F after literature review (Round 3)** | **3** | **1 / 12** (Forensics) |
| G Training-data provenance audit | 2 | 0 / 12 |
| **M Lab SME services (Round 4, Cycle 4)** | **3** | **3 / 12** (Abuse Investigator, RE, Detection Eng) |
| **N RE environments for labs (Round 5)** | **3.5** | **6 / 12** |
| **Q = N + M (Round 5)** | **4** | **7 / 12** (Abuse Investigator, Infra, RE, ML, Detection, Forensics, GTM) |
| O agent/MCP supply chain; P model scanning | 2.5; 2 | 1 / 12; 0 / 12 |
| V independent post-deployment cyber-misuse monitor (Round 6) | 4 | 7 / 12 |
| W = V + R, after iterations 19–23 (Round 6; withdrawn in Cycle 7, E96) | 4 | 9 / 12 |
| **Z independent malware-capability evaluator (Round 7)** | **4** | **8 / 12** (all except Abuse Investigator, Supply-Chain, Privacy Counsel, VC) |
| R alone / S alone / T / U (Cycle 6) | — | 6 / 5 / 2 / 1 of 12 |
| H / I / J / K / L (Cycle 4 components) | 3 / 3 / 3 / 2 / 2 | 2 / 2 / 1 / 0 / 0 |

- **No configuration reached consensus** (gate: ≥ 10/12 at ≥ 4). M is the first to pass the importance gate and the no-critical-legal-blocker gate.
- Unresolved critical blocker for F: A16 (legal).
- No votes were adjusted to meet thresholds.

### 10. Confidence

| Judgment | Confidence |
|---|---|
| Rejecting the original concept as a company | **Moderate–High** (convergent public evidence E02–E10 + E30b) |
| F as the best pivot direction | **Low** (Cycle 3: prior art, real-world performance gap, and EU legal limits. On the decision matrix F now scores 2.65 vs C's 2.85 on known criteria, within noise.) |
| Z's moat against labs (mandated independence, E90) | **Moderate–high** |
| Founder can deliver Z alone | **Moderate** (no network needed; track record must be built, X17) |
| Anyone pays for outside uplift adjudication | **Low** (A55 untested) |
| W's moat against **labs** (independence, victim-side and cross-provider evidence) | **Moderate–high** (primary texts E79–E83; E84, E85) |
| W's moat against **incumbents** (Google/Mandiant, Unit 42, TI vendors) | **Low** (H22; absence-of-evidence only, I23) |
| Labs buying W from a small specialist | **Low** (A45, A47, A51 untested; no buyer contact) |
| Q (RE environments + Safeguards services) as the best path to selling to frontier labs | **Moderate** for the budget and capability gap (E68–E75); **low** for this founder winning it (A38, A43, A44 untested; no buyer contact). |
| M (lab SME services) alone | **Low–moderate.** Need and buying channel are evidenced (E55–E61); WTP for this specific work, novelty of findings, and founder credibility are untested (A30–A33). |
| Any revenue forecast | **None made.** Insufficient evidence. |

### 11. Decision

| Option | Status |
|---|---|
| Original concept | **STOP** |
| **Z (Cycle 7)** | **PILOT FIRST**: X17–X19 and X11 (doc 13, Cycle 7 track) |
| W (Cycle 6) | **Withdrawn**: the founder cannot run its collection and supply networks (E96) |
| Q = N + M (Cycle 5) | Fallback: X9–X11 (doc 13, Cycle 5 track) |
| **Overall** | **PIVOT** to Z at PILOT FIRST. If X19 fails, fall back to M, then F (RESEARCH FIRST), then STOP. No N sales to labs Z evaluates. |
| G | **Not pursued** (membership-inference FPR 0.10; E48) |
| C / E | **BLOCKED** pending founder asset validation |
| D | **STOP** |

Build investment is locked behind Gates 1–3 (doc 13).

### 12. Next 3 experiments

1. **X1: real-binary benchmark (revised in Cycle 3).**
   - Datasets: the FSE 2026 public benchmark (E35), plus a proprietary-like split of real OSS functions transplanted into unrelated hosts, stripped, on x86_64 and ARM.
   - Baselines: B2SFinder, BAT, and our scoring-only slice. The candidate system adds a **local** verification stage.
   - **Pass:** recall ≥ 0.80, precision ≥ 0.95, and false-escalation rate ≤ 1%.
   - **Kill:** precision < 0.90 after verification, or recall < 0.60.
2. **X2: buyer discovery.**
   - 12 interviews with IP litigators, forensics experts, in-house IP counsel, and diligence providers, using the doc 10 question set.
   - **Pass:** ≥ 4 of 12 cite a binary/firmware case in the last 24 months **and** ≥ 3 offer data or a pilot. Then pursue 2 paid PoCs.
   - **Kill:** fewer than 4 cases, or no data offers.
3. **X3: counsel opinion** on lawful acquisition and analysis of third-party binaries (US §1201(f), EU Software Directive Art. 6, EULAs, chain of custody).
   - **Pass:** a lawful operating mode is defined.
   - **Kill:** no lawful mode exists in the primary market.

*Parallel:* run the doc 08 validation protocols on the founder's classifier and datasets once they are supplied.

---

## Document index

| Doc | Content |
|---|---|
| 01 | Intelligence requirements (PIR-1…12) |
| 02 | Evidence ledger (E01–E96, I01–I27) |
| 03 | Competitive landscape |
| 04 | Analysis of Competing Hypotheses (H1–H8) |
| 05 | Key assumptions, premortem, red team, signposts |
| 06 | Persona assessments |
| 07 | Voting matrix and gates |
| 08 | Technical feasibility and asset validation protocols |
| 09 | Benchmark design and measured results |
| 10 | Commercial validation plan |
| 11 | Feedback loops and decision matrix |
| 12 | MVP architecture |
| 13 | Gated roadmap |
| 14 | Peer-reviewed literature review (Cycle 3): binary→source SCA, binary similarity, birthmarks/plagiarism, watermarking, authorship, AI-code detection, training-data provenance, legal frameworks |

| 15 | Cycle 4: malware attribution sold to frontier labs. PIR-13–16, E51–E67, ACH H9–H13, KAC A29–A36, premortem P21–P27, red team, persona Round 4, iterations 9–13, matrix H–M, offer, discovery questions, X5–X7 |

| 16 | Cycle 5: pivot loop toward consensus. PIR-17–19, E68–E78, ACH H14–H17, KAC A37–A44, premortem P28–P33, red team, persona Round 5 with a consensus-ceiling table, iterations 14–18, matrix N–Q, X9–X11 |

| 17 | Cycle 6: what labs cannot replicate. PIR-20–22, E79–E89, replicability test across all candidates, ACH H18–H22, KAC A45–A52, premortem P34–P39, red team, persona Round 6, iterations 19–23, matrix under two weightings, X12 measured, X13–X16 |

| 18 | Cycle 7: founder-feasibility gate (W withdrawn), PIR-23–24, E90–E96, ACH H23–H26, KAC A53–A58, premortem P40–P44, red team, persona Round 7, iterations 24–28, matrix, X20 measured, X17–X19 |

Cycle 8 document: `research/19_cycle8_ten_more_ideas.md`.

Code: `provenance/` (vertical slice; `llm_indicators.py` for LLM-enabled malware indicators; `incident_packet.py` for consent-gated, provider-neutral incident evidence packets), `re_tasks/` (verifiable malware-RE task generator, grader and baselines; `evaluate.py` for evaluator controls: confidence intervals, canaries, per-customer partitions; `injection.py` for AI-analysis-evasion carriers, a detector and a verdict-flip harness), `bench/` (benchmark harnesses and results), `tests/`.
