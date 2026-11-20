# 06 — Independent Persona Assessments

> **Integrity notice.** These are 12 *simulated analytical perspectives* produced by one research process. They are not interviews with real experts. Their agreement is **not** independent empirical validation. Each persona was written using only the evidence ledger (doc 02) and measured results (doc 09), before the voting matrix was drafted. Personas cite evidence by `E-` ID. Where a persona asserts something without an ID, it is labelled *(judgment)*.

Two rounds:

- **Round 1** assesses the *original* proposal: an AI-provider-facing platform that attributes malicious code and binaries to generation sessions (Architectures A + B).
- **Round 2** reassesses the Cycle-2 pivot candidate **F: proprietary-code reuse detection in third-party compiled products** (IP investigation), after the feedback loop in doc 11.

---

## Persona 1 — AI Provider Abuse Investigator

**Round 1**

- *Would binary→session attribution improve investigations?* Marginally. Our cases start from on-platform signals: prompt content, account clusters, external TI overlap (E02, E03), or embedded API keys (E06). Artifact-first requests exist (E02's "cannot verify off-platform") but are not where our time goes *(judgment)*.
- *Unanswered questions today:* "Did this specific sample come from our outputs?" and "Which of our accounts produced the building blocks?" Both are rare and low priority once an account is already banned.
- *Is a ranked candidate list useful?* Only with explanations and a hard abstain. The slice's evidence-plus-abstain design is right, and 0/400 false escalations is encouraging (E30c). But the actors I care most about encrypt strings: escalation recall falls to 0.20 (E30b).
- *Access to retained records?* Default 30-day abuse logs and ZDR exclusions (E09) mean the record often no longer exists.
- *Actionable or speculative?* For naive actors, actionable leads. For sophisticated actors, speculative.
- **Strongest failure reason:** the records needed are gone by the time a sample surfaces, and the accounts were already banned from on-platform signals.

**Round 2 (F):** Outside my domain. Technically the same engine, with a better-matched adversary: infringers who rename but do not encrypt (E22). Neutral-positive.

## Persona 2 — Trust & Safety Engineering Lead

**Round 1**

- *Pipeline integration:* It would be another enrichment step behind existing classifiers; nothing upstream changes.
- *False accusations:* This is the dominant concern. The precision observed at threshold (1.0) is on synthetic negatives only (E30c). Shared or common code across users will create look-alike matches *(judgment)*, and lineage siblings already occupy rank 2 (E30, Lineage@1 > Recall@1).
- *Investigator efficiency:* Small. It is an occasional query tool.
- *Evidence thresholds:* Require ≥ 3 distinct high-IDF features plus a margin. The slice enforces this (`decide()`).
- *Auditability:* The hash-chained audit, case-gated queries, and query budget are appropriate (tests pass).
- **Strongest failure reason:** the risk of wrongly accusing a user is asymmetric to the investigative value gained.

**Round 2 (F):** False positives harm a *company relationship*, not an individual user. That is still serious, but outputs feed expert review, not automated action. More tolerable.

## Persona 3 — AI Infrastructure Architect

**Round 1**

- *Generation-time fingerprinting:* Feasible and cheap. About 116 features (≈ 1.5 KB) per record and sub-millisecond search at 10k records (E30). We already run comparable output matching for public code (E10).
- *Latency overhead:* Negligible if asynchronous after generation. Streaming outputs need assembly into artifacts first; agents produce multi-file diffs, which need per-file plus per-session records.
- *SDK deployment:* Must run in our VPC with our key. No third-party egress.
- *Storage:* At 1.5 KB per artifact, 1B artifacts ≈ 1.5 TB of keyed hashes. That is manageable, but it must honor ZDR (E09).
- *Language coverage:* C is easy. Python/JS ship as source, which is easier. Go/Rust binaries embed large runtimes *(judgment)*.
- **Strongest failure reason:** this is a two-sprint internal feature for us, not something we would buy (E10).

**Round 2 (F):** Same engine, deployed at the *IP owner* instead of a provider. The on-prem fingerprinting plus keyed-hash export pattern is sound (A21).

## Persona 4 — Malware Reverse Engineer

**Round 1**

- *PE/ELF/Mach-O:* The slice is ELF-only. PE needs import-table, resource, and .NET metadata handling. Mach-O needs LC_* and ObjC selectors *(judgment)*.
- *Compiler transforms:* Measured. Constants survive as immediates or ±1 compares. `printf` becomes `puts` and `fprintf` becomes `fwrite`. Dead branches vanish (observed during development). Opcode-sequence similarity collapses across optimization levels (E30e, consistent with E12).
- *Symbol stripping:* Kills `f:` features (symbols-only recall goes 0.83 → 0.0). Hybrid is unaffected because strings and constants survive (E30a).
- *Obfuscation and packing:* String encryption removes the strongest feature. Packing hides everything until unpacked. Real actors ask the model for exactly this (E05).
- *Decompiled similarity:* Not implemented. It is the next lever after strings and constants are gone (E11 shows it is hard).
- *Recoverability of source-level features:* Good for naive builds, poor for hostile ones.
- **Strongest failure reason:** the targets worth attributing are the ones that hide.

**Round 2 (F):** This is a much better fit. Shipping commercial products rarely encrypt every string. *Hytera* concealment was renaming (E22), which our features ignore. Firmware unpacking is mature (BANG, E29). My skills transfer directly.

## Persona 5 — Machine Learning Research Scientist

**Round 1**

- *Retrieval accuracy:* On synthetic data, hybrid R@10 ≥ 0.999 (default corpus) and 0.91 (boilerplate-heavy, stripped -O3) (E30). Learned function matching in the literature: R@1 ≈ 0.23 (E11).
- *Embedding / contrastive / graph:* Not run. Only an *untrained* sparse TF-IDF cosine was run; it slightly outperforms the summed-IDF ranker (E30). A learned model would need real paired data.
- *Dataset leakage:* Low here (index from source, queries from compiled artifacts, OOD generated separately). But **template leakage** is high: all programs come from 12 templates, which makes winnowing useless (R@1 0.04) and strings and constants over-distinctive.
- *Generalization:* Unseen projects only within one generator. Unseen model versions are **not tested**.
- *Open-set recognition:* Threshold calibrated on a split; 0/400 held-out false escalations, 95% upper bound ≈ 0.75% (rule of three). Encouraging, but the negatives come from the same generator.
- **Strongest failure reason:** the synthetic corpus overstates distinctiveness. Real performance is unknown.

**Round 2 (F):** Same caveats, plus IP-transplant R@10 drops from 1.0 to 0.66 under boilerplate (E30). The benchmark is a *valid experimental path* but not *valid for external claims* until rerun on real proprietary-like code.

## Persona 6 — Software Supply-Chain Security Researcher

**Round 1**

- *Ecosystems:* npm/PyPI ship source. Provenance by retrieval is easier there than for binaries (E28), but detection is the buyer's question, not provenance.
- *Malicious package discovery:* Crowded (E17, E18). The founder's dataset is absent (E01).
- *Package provenance:* SLSA/Sigstore answer "who built it". The proposal answers "which model session wrote it", which no defender workflow currently consumes *(judgment)*.
- *Reused malicious components / clustering:* Valuable, but already done (E20, E19).
- *Source vs binary evidence:* Source packages provide far better evidence.
- **Strongest failure reason:** "Which AI wrote this malicious package?" does not change the defender's response (block, rotate secrets).

**Round 2 (F):** Registries are a useful *monitoring surface* for leaked proprietary code (E24, E26), especially native addons, wheels with compiled extensions, and Electron/mobile bundles. This is a positive repurposing of supply-chain skills.

## Persona 7 — Detection Engineering Lead

**Round 1**

- *Telemetry integration:* Possible via the sample hash into the report. But provenance does not produce a detection.
- *Operational value:* Low. It does not change containment or eradication.
- *Alert precision / FP burden:* Abstain-by-default is right. But there is no alert to tune; this is a lookup.
- *IR workflow:* Fits only in attribution and intelligence write-ups.
- **Strongest failure reason:** provenance does not change a defender's response.

**Round 2 (F):** Continuous monitoring (new competitor firmware → scan → triage) is detection-engineering-shaped: thresholds, suppression, review queues. Fit is moderate.

## Persona 8 — Digital Forensics Investigator

**Round 1**

- *Chain of custody:* The slice records artifact SHA-256, case basis, actor, and decision in a tamper-evident chain. That is good.
- *Reproducibility:* Deterministic features, a fixed key, and a versioned extractor make it reproducible (the benchmark is reproducible from a seed).
- *Temporal correlation:* Not implemented. The session timestamp relative to the sample's first-seen date is a strong corroborator.
- *Alternative explanations:* Must be enumerated per E21 (third-party code, generators, common idioms, common author). The report template lists them.
- *Evidentiary limits:* A model session is not a person. Shared accounts, stolen keys, and reposted outputs all break the chain.
- **Strongest failure reason:** even a perfect match does not identify the human responsible.

**Round 2 (F):** This is the domain where the method already has standing. Experts present correlation evidence routinely, subject to excluding alternatives (E21, E22). The product would generate *leads and exhibits for an expert*, not conclusions.

## Persona 9 — Privacy and Data Protection Counsel *(not legal advice; qualified review required)*

**Round 1**

- *Data minimization:* Keyed hashes, no raw code, opaque refs. Directionally good.
- *Conversation privacy:* Fingerprints are *derived* from user content and may still be "customer content" under provider terms. ZDR customers' content cannot be retained (E09).
- *Retention/deletion:* TTL and deletion propagate in the slice (tested). They must match the provider's retention schedule.
- *Authorized access:* Case-gated, role-based, and budgeted. Good.
- *Cross-border:* An index holding EU users' derived data implicates transfer rules *(judgment)*.
- *Hash leakage:* Low-entropy features are reversible by the key holder (A21).
- **Strongest failure reason:** no provider will let a third party process session-derived data. A third-party vendor model is blocked (A3).

**Round 2 (F):** Better. The data subject is mostly corporate code, not personal conversations. The owner keeps the key. Open issue: **lawful acquisition and reverse engineering of third-party binaries** (A16) depends on jurisdiction and EULAs. This is a critical blocker until counsel opines.

## Persona 10 — AI Security CISO

**Round 1**

- *Business criticality:* Low. It does not prevent incidents.
- *Security outcomes:* Possible deterrence through attribution. Unproven.
- *Vendor risk:* High. The vendor would touch session-derived data.
- *Deployment:* On-prem only.
- *Budget ownership:* Unclear. T&S? Security? Legal?
- *Build vs buy:* Build (E10).
- **Strongest failure reason:** no budget line, and it is cheaper to build.

**Round 2 (F):** Budget sits with **General Counsel / IP**, not with me. I would support it, not buy it. Importance to my program: moderate.

## Persona 11 — Enterprise Procurement & GTM Specialist

**Round 1**

- *Buyer:* About 6–15 organizations worldwide (FMF members plus coding-tool vendors) (E08).
- *Sales cycle:* Long. Security review of a vendor touching model outputs.
- *Willingness to pay:* No signal (PIR-5).
- *Pricing:* Unknown. No comparable public prices.
- *Positioning:* Against in-house teams.
- *Procurement barriers:* DPA, security review, and data residency.
- *Design partners:* Possible via the founder's TI network, but the ask ("share session-derived data") is the hardest possible ask.
- **Strongest failure reason:** a tiny market of sophisticated builders.

**Round 2 (F):** Plausible buyers exist:

- IP litigation boutiques and AmLaw litigation groups.
- Software-forensics expert firms (E21).
- In-house IP counsel at embedded/OEM, gaming, and security-software firms.
- M&A diligence teams.

Purchasing could run as per-matter engagements (litigation budgets) evolving to monitoring subscriptions. Damages scale supports it (E22, E23). **No commitment yet.**

## Persona 12 — Skeptical Venture Investor

**Round 1**

- *Market size:* Too small; the buyer count is in the low tens.
- *Defensibility:* None algorithmic (E29). Providers own the data.
- *Founder-market fit:* Good technical fit, weak buyer access.
- *Scalability:* Bespoke integrations per provider.
- *Distribution:* None.
- *Revenue potential:* Low.
- *Failure scenario:* P1 + P2 (doc 05).
- **Strongest failure reason:** the customer can build it, and the adversary can evade it.

**Round 2 (F):** This is a real wedge with real dollars at stake per case (E22, E23). But it risks being a services business with lumpy revenue (P9) and incumbent bundling (P11). Fundable only after evidence of repeatable, paid usage.
