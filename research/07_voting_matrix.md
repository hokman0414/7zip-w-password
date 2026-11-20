# 07 — Persona Voting Matrix

> Votes are simulated analytical judgments (see doc 06 notice). A score without cited evidence is invalid and was not admitted. Scores are 1 = strongly unfavorable … 5 = strongly favorable.

Dimensions: **Imp** problem importance · **Tech** technical feasibility · **Dem** commercial demand · **Def** defensibility · **Priv** privacy/legal feasibility · **Fdr** founder advantage · **Adopt** customer adoption probability · **Ovr** overall investment attractiveness.

## Round 1 — Original proposal (AI-provider binary→generation-session attribution platform)

| # | Persona | Imp | Tech | Dem | Def | Priv | Fdr | Adopt | **Ovr** | Conf. |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Abuse Investigator | 3 | 3 | 2 | 2 | 2 | 3 | 2 | **2** | Moderate |
| 2 | T&S Eng Lead | 2 | 3 | 2 | 2 | 2 | 2 | 2 | **2** | Moderate |
| 3 | Infra Architect | 2 | 4 | 2 | 1 | 3 | 2 | 2 | **2** | High |
| 4 | Malware RE | 3 | 2 | 2 | 2 | 3 | 4 | 2 | **2** | High |
| 5 | ML Scientist | 3 | 3 | 2 | 1 | 3 | 2 | 2 | **2** | Moderate |
| 6 | Supply-Chain Researcher | 2 | 3 | 2 | 2 | 3 | 3 | 2 | **2** | Moderate |
| 7 | Detection Eng Lead | 2 | 3 | 2 | 2 | 3 | 3 | 2 | **2** | Moderate |
| 8 | Forensics Investigator | 3 | 3 | 2 | 2 | 2 | 3 | 2 | **2** | Moderate |
| 9 | Privacy Counsel | 2 | 3 | 2 | 2 | **1** | 2 | 2 | **1** | Moderate |
| 10 | AI Security CISO | 2 | 3 | 1 | 2 | 2 | 2 | 1 | **1** | High |
| 11 | Procurement/GTM | 2 | 3 | 1 | 2 | 2 | 2 | 1 | **1** | High |
| 12 | Skeptical VC | 2 | 3 | 1 | 1 | 2 | 3 | 1 | **1** | High |
| | **Median** | 2 | 3 | 2 | 2 | 2 | 2.5 | 2 | **2** | |

### Round 1 vote justifications

| # | Evidence supporting score | Evidence against score | Critical blockers | Would change vote if… |
|---|---|---|---|---|
| 1 | On-platform attribution already works (E02, E03, E06); retention gaps (E09) | Off-platform verification gap is real (E02) | Records expire before samples surface | Providers report ≥ monthly artifact-first requests |
| 2 | False-accusation asymmetry; synthetic-only negatives (E30c) | Precision 1.0 at threshold (E30c) | No real-data FPR | Real-data FPR ≤ 0.5% with human review |
| 3 | In-house pattern exists (E10); cheap to build (E30 cost) | — | Build-vs-buy | Provider asks for a vendor SDK |
| 4 | Obfuscation is requested by actors (E05); measured collapse (E30b) | Strong on naive builds (E30a) | Packing/encryption | Recall ≥ 0.6 on obfuscated real samples |
| 5 | Template bias; untrained baselines only (E30) | Calibrated open-set (E30c) | No real paired data | Real-output benchmark R@10 ≥ 0.85 |
| 6 | Crowded market (E17, E18) | Source packages are easier (E28) | Provenance ≠ action | Defenders show a changed action from provenance |
| 7 | No detection outcome | — | No alert use-case | IR teams request it for attribution reporting |
| 8 | Session ≠ person; alternative explanations (E21) | Reproducible features, audit chain (tests) | Identity gap | Linking to account-level evidence becomes possible |
| 9 | Third-party processing of session-derived data blocked (E09, A3) | Keyed hashing design (A21) | **Critical legal/privacy blocker** | Provider-hosted, provider-keyed deployment only |
| 10 | No budget owner; build cheaper (E10) | — | Budget | Board-level attribution mandate |
| 11 | ≈ 6–15 buyers (E08); no buyer signal (PIR-5) | Providers do buy security tools (E17) | Market size | ≥ 3 providers commit to paid pilots |
| 12 | No moat (E29); tiny TAM | Founder fit technically | Market + moat | Evidence of a large adjacent market using the same core |

### Round 1 consensus gates

| Gate | Result |
|---|---|
| All 12 independent assessments completed | **Pass** |
| No unresolved critical legal/privacy blocker | **Fail** (Persona 9: third-party processing of session data) |
| Credible experimental validation path | **Pass** (benchmark harness exists; real-data rerun defined) |
| ≥ 10/12 overall ≥ 4 | **Fail** (0/12) |
| CISO and Abuse Investigator importance ≥ 4 | **Fail** (2 and 3) |
| ML + RE agree the benchmark is scientifically valid | **Partial**: valid *path*, not valid for external claims (template bias, synthetic negatives) |
| Procurement identifies a plausible buyer and process | **Fail** |

**Outcome: the original proposal does not advance.** This triggered the Phase 9 feedback loop (doc 11).

---

## Round 2 — Pivot candidate F (proprietary-code reuse detection in third-party compiled products)

| # | Persona | Imp | Tech | Dem | Def | Priv | Fdr | Adopt | **Ovr** | Conf. |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Abuse Investigator | 3 | 4 | 3 | 3 | 3 | 4 | 3 | **3** | Low |
| 2 | T&S Eng Lead | 3 | 4 | 3 | 3 | 3 | 3 | 3 | **3** | Low |
| 3 | Infra Architect | 3 | 4 | 3 | 2 | 4 | 3 | 3 | **3** | Moderate |
| 4 | Malware RE | 4 | 4 | 3 | 3 | 3 | **5** | 3 | **4** | Moderate |
| 5 | ML Scientist | 3 | 4 | 3 | 2 | 4 | 3 | 3 | **3** | Moderate |
| 6 | Supply-Chain Researcher | 4 | 4 | 3 | 3 | 3 | 4 | 3 | **3** | Low |
| 7 | Detection Eng Lead | 3 | 4 | 3 | 3 | 3 | 4 | 3 | **3** | Low |
| 8 | Forensics Investigator | 4 | 3 | 3 | 3 | 3 | 4 | 3 | **4** | Moderate |
| 9 | Privacy Counsel | 3 | 4 | 3 | 3 | **3** | 3 | 3 | **3** | Low |
| 10 | AI Security CISO | 3 | 4 | 2 | 3 | 3 | 3 | 2 | **3** | Moderate |
| 11 | Procurement/GTM | 4 | 4 | 3 | 3 | 3 | 3 | 3 | **3** | Low |
| 12 | Skeptical VC | 3 | 4 | 3 | 2 | 3 | 4 | 2 | **3** | Moderate |
| | **Median** | 3 | 4 | 3 | 3 | 3 | 3.5 | 3 | **3** | |

### Round 2 vote justifications

| # | Evidence supporting score | Evidence against score | Critical blockers | Would change vote if… |
|---|---|---|---|---|
| 1 | Better-matched adversary (E22) | Out of domain | — | — |
| 2 | Output goes to expert review, not automated action | FP harm to company relationships | — | Real-data precision ≥ 0.95 |
| 3 | On-prem keyed fingerprinting works (A21, tests) | Incumbents could add it (A19) | — | — |
| 4 | Renaming-only concealment survived (E22, E30d); firmware tooling mature (E29) | Boilerplate-heavy IP recall 0.66 (E30) | Packed firmware | Real-firmware pilot R@10 ≥ 0.8 |
| 5 | Measured transplant R@10 = 1.0 default (E30d) | 0.66 under boilerplate; synthetic only | Benchmark validity | Rerun on real OSS-as-proxy proprietary code |
| 6 | Registries as monitoring surface (E24, E26) | Source monitoring commoditized (E26) | — | Registry pilot finds a real leak |
| 7 | Monitoring workflow fits DE practice | Low frequency | — | — |
| 8 | Established evidentiary use (E21, E22) | Must exclude alternatives | Admissibility untested | Expert endorses a sample report |
| 9 | Corporate code, owner-held key | Lawful acquisition/RE of third-party binaries (A16) | **Critical until counsel opines** | Favourable counsel opinion in target jurisdictions |
| 10 | Real IP loss scale (E22, E23) | Budget is Legal's, not CISO's | — | GC sponsor identified |
| 11 | Plausible buyers and per-matter purchasing (E21, E23) | No commitments | — | 2 paid PoCs |
| 12 | Large per-case value (E22, E23) | Services risk, incumbents (P9, P11) | — | Evidence of recurring subscription demand |

### Round 2 consensus gates

| Gate | Result |
|---|---|
| All 12 assessments completed | **Pass** |
| No unresolved critical legal/privacy blocker | **Fail** (A16: lawful acquisition/analysis of third-party binaries, pending counsel) |
| Credible experimental validation path | **Pass** |
| ≥ 10/12 overall ≥ 4 | **Fail** (2/12) |
| CISO and Abuse Investigator importance ≥ 4 | **Fail** (3 and 3). Arguably the wrong gatekeepers for an IP product; the Forensics and RE personas are the domain owners. Recorded, but the gate is **not waived**. |
| ML + RE agree benchmark is valid | **Partial** (valid path, not valid for external claims) |
| Procurement identifies plausible buyer/process | **Pass (conditional)**: IP litigation counsel and forensics firms, per-matter |

**Outcome: Candidate F does not meet the consensus threshold either.** It is the highest-scoring candidate. Its failures are **evidence gaps** (demand, legal opinion, real-data benchmark), not demonstrated fundamental flaws. Per Phase 9, the next step is evidence collection, not building.

---

## Overall-attractiveness vote across all candidate configurations (after feedback loop)

Each cell is the persona's Ovr score with the same evidence discipline. `U` = UNKNOWN (persona judged evidence insufficient to score).

| Persona | A Provider SDK | B Binary→source platform | C Supply-chain provenance intel | D Coding-agent observability | E Hybrid malware intel + provenance | F IP code-reuse investigation |
|---|---|---|---|---|---|---|
| 1 Abuse Inv. | 2 | 2 | 2 | 2 | 2 | 3 |
| 2 T&S Eng | 2 | 2 | 2 | 3 | 2 | 3 |
| 3 Infra Arch | 2 | 2 | 2 | 2 | 2 | 3 |
| 4 Malware RE | 2 | 2 | 3 | 2 | 3 | 4 |
| 5 ML Sci | 2 | 2 | 2 | 2 | 2 | 3 |
| 6 Supply Chain | 1 | 2 | 3 | 2 | 2 | 3 |
| 7 Detection Eng | 1 | 2 | 3 | 2 | 3 | 3 |
| 8 Forensics | 2 | 3 | 2 | 2 | 2 | 4 |
| 9 Privacy | 2 | 2 | 3 | 2 | 2 | 3 |
| 10 CISO | 1 | 1 | 2 | 3 | 2 | 3 |
| 11 GTM | 1 | 1 | 2 | 2 | 1 | 3 |
| 12 VC | 1 | 1 | 2 | 2 | 1 | 3 |
| **# ≥ 4** | 0 | 0 | 0 | 0 | 0 | **2** |
| **Median** | 2 | 2 | 2 | 2 | 2 | **3** |

D scores 2 because the category is crowded and well-funded (E27), and the founder's assets do not apply. C and E score 2 because the market is crowded (E17, E18) and the founder's assets are unvalidated (E01).

**No configuration achieves consensus. No positive votes were manufactured to meet the threshold.**

---

## Round 3 — Candidate F after the peer-reviewed literature review (doc 14)

Votes are re-cast only where the new evidence (E32–E50) changes a persona's judgment. Unchanged rows are re-confirmed, not copied blindly. Each was checked against E35/E36 (real-world performance) and E50 (legal).

| # | Persona | Imp | Tech | Dem | Def | Priv | Fdr | Adopt | **Ovr** | Change driver |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Abuse Investigator | 3 | 3 | 3 | 2 | 3 | 4 | 3 | **3** | E35 (Tech), E32/E33 (Def) |
| 2 | T&S Eng Lead | 3 | 3 | 3 | 2 | 3 | 3 | 3 | **3** | E36 (precision needs verification) |
| 3 | Infra Architect | 3 | 4 | 3 | 2 | 4 | 3 | 3 | **3** | E36 (local open-weight verification feasible) |
| 4 | Malware RE | 4 | 3 | 3 | 2 | 3 | 5 | 3 | **3** (↓ from 4) | E32 near-identical prior art; B2SFinder 19.9% recall (E36) |
| 5 | ML Scientist | 3 | 3 | 3 | 2 | 4 | 3 | 3 | **3** | A25 fails (E35–E37) |
| 6 | Supply-Chain Researcher | 4 | 3 | 3 | 2 | 3 | 4 | 3 | **3** | E37 domain-specific < 45% |
| 7 | Detection Eng Lead | 3 | 3 | 3 | 2 | 3 | 4 | 3 | **3** | E35 (Tech), E32/E33 (Def) |
| 8 | Forensics Investigator | 4 | 3 | 3 | 3 | 3 | 4 | 3 | **4** | E36 verification + E50a filtration fit an expert workflow |
| 9 | Privacy Counsel | 3 | 3 | 3 | 2 | **2** | 3 | 2 | **2** (↓ from 3) | E50d: EU decompilation is interoperability-only |
| 10 | AI Security CISO | 3 | 3 | 2 | 2 | 3 | 3 | 2 | **3** | Budget still Legal's |
| 11 | Procurement/GTM | 4 | 3 | 3 | 2 | 3 | 3 | 3 | **3** | Competing binary SCA vendors (E33, E37) |
| 12 | Skeptical VC | 3 | 3 | 3 | **1** | 3 | 4 | 2 | **2** (↓ from 3) | A19 fails (E33, E36) |
| | **Median** | 3 | 3 | 3 | 2 | 3 | 3.5 | 3 | **3** | |

**Round 3 gates:**
- Overall ≥ 4: **1/12 (fail).**
- Critical legal blocker (A16): **unresolved and more severe (fail).**
- ML + RE agree the benchmark is valid: **fail.** The synthetic results are contradicted by real-world studies; the revised X1 is the valid path.

**Outcome: no consensus. No votes were raised to meet the threshold.**

Candidate G (training-data provenance audit) was assessed once (doc 14 §7): **median Ovr 2, 0/12 at ≥ 4.**

