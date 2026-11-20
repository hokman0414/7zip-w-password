# EXECUTIVE DECISION

## Decision: **PIVOT**

The original concept, an AI Code Provenance and Malware-to-Generation Attribution platform sold to AI providers, is **not** a viable standalone business on current evidence.

The pivot target is **IP code-reuse investigation**: detecting a company's proprietary code inside third-parties' compiled products. This target is at **RESEARCH FIRST** status (downgraded from PILOT FIRST after the Cycle 3 peer-reviewed literature review, doc 14). **No platform build is authorized** until the three experiments below pass their gates.

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

AI providers are **not** the target. Buyers are few, they build in-house, and session data cannot leave them (doc 11, iteration 1).

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

- **No configuration reached consensus** (gate: ≥ 10/12 at ≥ 4).
- Unresolved critical blocker for F: A16 (legal).
- No votes were adjusted to meet thresholds.

### 10. Confidence

| Judgment | Confidence |
|---|---|
| Rejecting the original concept as a company | **Moderate–High** (convergent public evidence E02–E10 + E30b) |
| F as the best pivot direction | **Low** (Cycle 3: prior art, real-world performance gap, and EU legal limits. On the decision matrix F now scores 2.65 vs C's 2.85 on known criteria, within noise.) |
| Any revenue forecast | **None made.** Insufficient evidence. |

### 11. Decision

| Option | Status |
|---|---|
| Original concept | **STOP** |
| **Overall** | **PIVOT** to F at **RESEARCH FIRST**. If F fails X1 or X2, the default is STOP. |
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
| 02 | Evidence ledger (E01–E50, I01–I09) |
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

Code: `provenance/` (vertical slice), `bench/` (benchmark harness and results), `tests/`.
