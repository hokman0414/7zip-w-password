# 05 — Key Assumptions Check, Premortem, Red Team, Indicators & Signposts

## Key Assumptions Check (24 assumptions)

Columns: why it matters / supporting / contradicting / testability / cost of validation (S = days, M = weeks, L = months or significant money) / consequence if false. Status: **Holds**, **Weak**, **Fails**, **Untested**.

| # | Assumption | Why it matters | Supporting | Contradicting | Testable? | Cost | If false | Status |
|---|---|---|---|---|---|---|---|---|
| A1 | Providers frequently receive artifact-first investigations ("did your model write this?") | Core demand for original concept | E02 off-platform gap | E02–E06 all on-platform-first | Yes: interviews | S | Original product has no demand | **Weak** |
| A2 | Providers cannot or will not build artifact→session matching themselves | Vendor viability | none | E10 (they already build output matching) | Yes | S | Build-vs-buy kills vendor | **Fails** |
| A3 | Providers would share session-derived data with a vendor | SaaS architecture | none | E09 retention and ZDR; PIR-4 | Yes: DPO interview | S | Must be on-prem software | **Fails** (for SaaS) |
| A4 | Generated code survives into deployed malware largely intact | Retrieval signal exists | E28 (comments left in) | E02 (building blocks assembled), E05 (obfuscation requested) | Yes | M | Retrieval mostly misses | **Weak** |
| A5 | Distinctive strings/constants survive compilation | Feature basis | E30a (≥0.99 R@10 unobfuscated) | E30b; boilerplate-heavy run | Done | — | Need learned features | **Holds** (naive), **Fails** (adversarial) |
| A6 | Real LLM output is as distinctive as our synthetic corpus | Benchmark validity | none | Boilerplate-heavy run cuts stripped R@10 to 0.91 and IP-transplant to 0.66 | Yes: real outputs | M | Measured numbers are optimistic | **Untested, likely optimistic** |
| A7 | One session maps to one artifact | Ranking semantics | — | E02 (multi-session), E04 (multi-provider) | Yes | M | Need set/containment retrieval | **Fails** in general |
| A8 | Retention windows cover investigation latency | Records exist when needed | — | E09 (30 days default; ZDR) | Yes | S | Most records gone | **Weak** |
| A9 | A ranked candidate list is actionable for T&S | Output usefulness | Investigators use leads | E21 alternative explanations; false-accusation risk | Yes: workflow test | M | Product is noise | **Untested** |
| A10 | Open-set rejection keeps false escalation ≤ 1% | Safety | E30c (0/400; 95% upper bound ≈ 0.75%) | Synthetic negatives only | Yes | M | Harm from false accusations | **Holds on synthetic data** |
| A11 | The founder's classifier is accurate on unseen families | Asset value | Founder claim | E01 (absent); 0-VT ≠ malicious | Yes (protocol in doc 08) | M | No asset advantage | **Untested** |
| A12 | The founder's datasets are licensed and representative | Asset value | Founder claim | E01 | Yes | S | Legal exposure, no moat | **Untested** |
| A13 | Supply-chain buyers will pay for *provenance* in addition to detection | H4/H7 demand | E17 (market real) | No evidence provenance changes defender action | Yes: interviews | S | Feature, not product | **Weak** |
| A14 | IP owners want to find their code in third-party compiled products | H8 demand | E22, E23 | Episodic; experts may suffice | Yes: interviews | S | H8 fails | **Untested, plausible** |
| A15 | IP owners accept on-prem fingerprinting (source never leaves) | H8 privacy | E16 (FOSSA ships fingerprints already) | Some will not install anything | Yes | S | Must offer a services model | **Plausible** |
| A16 | Third-party binaries can be lawfully acquired and analyzed for this purpose | H8 legality | Common in litigation support | EULA anti-RE clauses; jurisdiction-specific | Yes: counsel | M | Restricted to litigation discovery | **Untested** |
| A17 | Infringers often do not obfuscate | H8 technical | E22 (renaming, not obfuscation) | Sophisticated actors would | Yes: case study review | M | Same failure mode as malware | **Plausible** |
| A18 | Output can support pre-filing decisions or expert reports | H8 value | E23 (early trade-secret identification) | E21 (must exclude alternatives) | Yes: expert review | S | Lead-gen only | **Untested** |
| A19 | Incumbents (Black Duck, Cycode, RL) will not quickly add "your private code in binaries" | Defensibility | Not offered today (unverified for Black Duck) | They have the tech | Partially | S | Squeezed | **Weak** |
| A20 | The method is novel enough to defend | Moat | — | E29 (BAT 2011), E11 | Done | — | Moat must be data/workflow | **Fails** (algorithmic novelty) |
| A21 | Keyed hashing prevents leakage of indexed content | Privacy claim | HMAC design; test passes | Low-entropy features are dictionary-attackable by key holders | Yes | S | Must keep key with data owner | **Holds** with key-custody constraint |
| A22 | Search latency/cost is not a constraint at 10k–1M records | Ops | E30: 0.3 ms median search at 10k; 1.5 KB/record | Learned models would cost more | Done (10k) | S | — | **Holds** at 10k |
| A23 | Watermarking will not make the product obsolete | Competitive | E13 (watermarks fragile) | Provider-side watermarking may improve | Monitor | — | Commoditized | **Holds (for now)** |
| A24 | The founder can sell to legal/IP buyers | GTM | RE + forensics background fits | Security founders often struggle with legal buyers | Yes: 10 calls | S | Need a legal-domain co-founder | **Untested** |

## Premortem — "It is November 2028 and the company has failed. Why?"

Likelihood (L) and severity (S) are rated 1–5. Detectability (D) is rated 1–5, where 5 means easy to detect early. **Risk priority** = L × S × (6 − D).

| # | Failure cause | L | S | D | RPN | Early warning |
|---|---|---|---|---|---|---|
| P1 | Providers built it in-house (or didn't need it); no provider ever bought | 5 | 5 | 4 | 50 | No pilot after 10 provider calls |
| P2 | Real adversaries obfuscated; retrieval found nothing that mattered | 4 | 5 | 3 | 60 | Real-sample recall < 30% |
| P3 | Synthetic benchmark overstated performance; real code too generic | 4 | 4 | 3 | 48 | Real-output R@10 < 70% |
| P4 | A false attribution reached a customer and caused reputational/legal harm | 2 | 5 | 2 | 40 | Any wrong escalation in pilot |
| P5 | Session data could not leave providers; no access, no product | 4 | 5 | 4 | 40 | DPO says no |
| P6 | Founder classifier failed independent validation; credibility lost | 3 | 3 | 4 | 18 | FPR > 1% on benign corpus |
| P7 | Datasets had licensing problems | 2 | 4 | 4 | 16 | Missing provenance docs |
| P8 | Pivoted into supply chain; out-competed by Socket/Checkmarx/JFrog | 4 | 4 | 4 | 32 | Head-to-head losses |
| P9 | IP buyers preferred hourly experts; no recurring revenue | 3 | 4 | 3 | 36 | Pilots convert to one-off services |
| P10 | Sales cycles with legal/IP buyers exceeded runway | 3 | 4 | 3 | 36 | > 9-month cycles in first 5 deals |
| P11 | Black Duck/Cycode added the feature and bundled it | 3 | 4 | 2 | 48 | Product announcements |
| P12 | Lawful acquisition of third-party binaries was blocked by counsel or EULAs | 2 | 4 | 4 | 16 | Counsel opinion |
| P13 | Evidence was not accepted by experts or courts | 2 | 4 | 3 | 24 | Expert feedback on sample reports |
| P14 | Built a broad platform before validating one buyer | 3 | 4 | 4 | 24 | Roadmap > 3 modules before first paid pilot |
| P15 | Key person risk: single founder is both researcher and seller | 3 | 3 | 4 | 18 | Pipeline stalls during build sprints |
| P16 | PE/Mach-O, packed, Go/Rust binaries performed far worse than ELF/C | 4 | 3 | 3 | 36 | Format-specific recall gaps |
| P17 | Privacy regulators/customers treated fingerprints as personal data | 2 | 3 | 3 | 18 | DPA negotiation friction |

**Top five by RPN:** P2 (adversarial obfuscation), P1 (no provider buyer), P3 (benchmark optimism), P11 (incumbent bundling), P5 (no data access). P2 and P3 also apply to the IP pivot, with lower likelihood (A17).

## Red Team

| Target | Challenge | Response / residual risk |
|---|---|---|
| **Novelty** | String/constant binary→source matching is BAT (2011). Learned matching is BinaryAI (2024). Snippet IP matching is Black Duck/SCANOSS. | Conceded. **There is no algorithmic moat.** Any moat must come from workflow (privacy-preserving custody, evidence packaging), proprietary corpora, and trust with legal buyers. |
| **Attribution reliability** | Matching a binary to a session proves neither who ran the session nor who deployed the binary. Code is shared, reposted, and regenerated. | The slice reports candidates and abstains by default. Reports carry explicit limitations (`provenance/report.py`). Residual risk: users over-read rankings. |
| **Privacy** | Fingerprints derive from customer content. Key holders can dictionary-attack low-entropy features. | Key stays with the data owner. Only keyed hashes move. Residual: legal classification of fingerprints is unresolved (counsel needed). |
| **Market demand** | No buyer has said yes. Personas are not customers. | Conceded. Every demand claim in docs 06–07 is labelled simulated. Doc 10 defines the real tests. |
| **Model performance** | Benchmark is synthetic, C-only, ELF-only, x86-64-only, single compiler version per family, template-generated. Winnowing could not discriminate because templates share structure. | Conceded; quantified in doc 09. The boilerplate-heavy run shows the direction of the bias. |
| **Customer access** | Providers (original) and litigators (pivot) are hard to reach. | Founder network in TI/RE is relevant to forensic experts. Legal buyers still need warm intros. |
| **Data quality** | Founder datasets unseen (E01). | Treated as zero until validated. |
| **Competitive advantage** | Incumbents have larger corpora (E18, E19) and existing customers. | For H8, the corpus that matters is the *customer's own* code, which no incumbent has either. The advantage is narrow but real if validated. |
| **Red-team the pivot** | "Find my code in their binary" is a 2–3-week expert engagement today. Why would anyone subscribe? | Possible answers: continuous monitoring of competitor firmware/app releases and registries; pre-filing triage at lower cost; M&A diligence. **Unvalidated.** |

## Indicators and signposts

| Signpost | ↑ confidence if… | ↓ confidence if… |
|---|---|---|
| Provider interest (original) | A provider T&S lead names a budget owner and shares sample cases | Providers say "we already do this" or "logs are 30-day/ZDR" |
| Design-partner commitments (pivot) | ≥ 2 IP-owner or law-firm partners provide fingerprints of their own code plus suspect artifacts | Only "send us a report when it's ready" |
| Paid PoC | ≥ 1 paid PoC at ≥ $15k within 6 months of starting discovery (target, not an estimate of market price) | Only free pilots |
| Benchmark | Real-output R@10 ≥ 0.85 on stripped -O2 with false escalation ≤ 1% | R@10 < 0.7 or any wrong escalation |
| Competitor releases | Incumbents stay source/OSS-only | Black Duck/Cycode/RL announce private-code binary matching |
| Regulation | Courts/agencies cite binary-forensics evidence; EU AI Act transparency obligations increase demand for provenance | Courts reject similarity evidence; privacy rulings treat fingerprints as personal data |
| Infrastructure integration | Providers expose provenance hooks/APIs | Providers lock outputs behind ZDR by default |
| Founder assets | Classifier passes temporal-holdout validation; datasets have clear licences | Validation fails or licensing is unclear |

## Cycle 3 assumption updates (literature; see doc 14 §5)

| ID | Assumption | Status after Cycle 3 |
|---|---|---|
| A16 | Lawful acquisition and analysis of third-party binaries | **Doubtful in the EU** for static decompilation (Art. 6 is interoperability-only); fact-specific in the US (E50). Still critical. |
| A19 | Incumbents will not add compiled-artifact matching | **Fails** (E33, E36, E37) |
| A20 | Method novelty | **Fails more strongly** (B2SFinder, E32) |
| A25 | Synthetic results transfer to real binaries | **Fails as stated** (E35–E37) |
| A26 | Proprietary code is more distinctive than OSS after suppression (I08) | **Untested.** Gating. |
| A27 | Verification can run locally without external AI services | **Plausible** (E36 open-weight results) |
| A28 | Stylometry can support provenance claims | **Rejected as evidence** (E45) |

New premortem causes:

| # | Cause | L | S | D | RPN | Early warning |
|---|---|---|---|---|---|---|
| P18 | Real binaries yield about 20–60% recall; the product misses most reuse (E35, E36) | 4 | 5 | 3 | 60 | Revised X1 recall < 0.6 |
| P19 | A deployed binary SCA vendor (BinaryAI- or BLADE-class) adds "index your own code" | 4 | 4 | 2 | 64 | Vendor announcement |
| P20 | EU clients cannot lawfully decompile suspect products for this purpose | 3 | 4 | 3 | 36 | Counsel opinion (X3) |

## Cycle 4 update (frontier-lab SME services, doc 15 §7–§9)

| ID | Assumption | Status |
|---|---|---|
| A29 | Lab misuse-investigation workload exceeds in-house capacity | Plausible (E58 contractors) |
| A30 | Labs will contract a small firm, not only marketplace individuals | **Untested** |
| A31 | Keys found in malware are not already systematically reported and revoked | **Untested** (E54, E63 scope gap) |
| A32 | Public sample sources without VirusTotal contain enough LLM-enabled samples | **Untested** |
| A33 | Lab Safeguards teams recognize the founder's credibility | **Untested** |
| A34 | Model-level code attribution is usable as a lead | Plausible as a lead; doubtful under adversaries (E45, E65) |
| A35 | Disclosure-only handling of found credentials has no critical legal blocker | Plausible; counsel needed |
| A36 | Google and Microsoft are not realistic buyers | Plausible (in-house threat intelligence) |

| # | Cause | L | S | D | RPN | Early warning |
|---|---|---|---|---|---|---|
| P21 | Labs cover everything in-house plus FMF sharing | 4 | 5 | 3 | **60** | X6: < 2 of 10 describe a gap |
| P22 | Vendors give labs this intel free | 4 | 4 | 3 | 48 | X5 novelty low |
| P23 | Work is bought as commodity hourly labour | 3 | 3 | 2 | 36 | Only marketplace-rate offers |
| P26 | Malware moves to local models, proxies or stolen keys (T1 signal decays) | 3 | 4 | 3 | 36 | Vendor reports |
| P25 | Public overclaim of model attribution | 2 | 5 | 3 | 30 | Any "authorship" wording in a deliverable |
| P24 | Credential or sample mishandling incident | 2 | 5 | 4 | 20 | Any full key stored or tested |
| P27 | Founder conflicts block contracting | 2 | 4 | 4 | 16 | Pre-outreach check |

Red team (doc 15 §9): an embedded key can belong to a **victim** whose key was stolen. A key → account link is a lead for the provider to review, never attribution of the author.

Signpost triggered: "Providers publish artifact-first attribution cases" (doc 13). Anthropic (E55) and OpenAI (E57) now describe artifact↔generation checks. These are handled in-house, so the signpost re-opens the need as **services**, not as a tool.
