# EXECUTIVE DECISION

## Decision: **PIVOT** — to malware-RE training environments and evaluations for frontier labs, with Safeguards SME services (**PILOT FIRST**)

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
| H / I / J / K / L (Cycle 4 components) | 3 / 3 / 3 / 2 / 2 | 2 / 2 / 1 / 0 / 0 |

- **No configuration reached consensus** (gate: ≥ 10/12 at ≥ 4). M is the first to pass the importance gate and the no-critical-legal-blocker gate.
- Unresolved critical blocker for F: A16 (legal).
- No votes were adjusted to meet thresholds.

### 10. Confidence

| Judgment | Confidence |
|---|---|
| Rejecting the original concept as a company | **Moderate–High** (convergent public evidence E02–E10 + E30b) |
| F as the best pivot direction | **Low** (Cycle 3: prior art, real-world performance gap, and EU legal limits. On the decision matrix F now scores 2.65 vs C's 2.85 on known criteria, within noise.) |
| Q (RE environments + Safeguards services) as the best path to selling to frontier labs | **Moderate** for the budget and capability gap (E68–E75); **low** for this founder winning it (A38, A43, A44 untested; no buyer contact). |
| M (lab SME services) alone | **Low–moderate.** Need and buying channel are evidenced (E55–E61); WTP for this specific work, novelty of findings, and founder credibility are untested (A30–A33). |
| Any revenue forecast | **None made.** Insufficient evidence. |

### 11. Decision

| Option | Status |
|---|---|
| Original concept | **STOP** |
| **Q = N + M (Cycle 5)** | **PILOT FIRST**: X9–X11 (doc 13, Cycle 5 track) plus X5/X6 for the M component |
| **Overall** | **PIVOT** to Q at PILOT FIRST, with F at **RESEARCH FIRST** as the fallback. If X10 fails, fall back to M (if X5/X6 pass), then F, then STOP. |
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
| 02 | Evidence ledger (E01–E78, I01–I18) |
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

Code: `provenance/` (vertical slice; `llm_indicators.py` for LLM-enabled malware indicators), `re_tasks/` (verifiable malware-RE task generator, grader and baselines), `bench/` (benchmark harnesses and results), `tests/`.
