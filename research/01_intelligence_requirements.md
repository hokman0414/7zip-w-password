# 01 — Intelligence Requirements

## Intelligence cycle used

`Direction (PIRs) → Collection (repo inspection, open-source web research, measured benchmark) → Processing (evidence ledger, credibility grading) → Analysis (ACH, KAC, premortem, red team, personas) → Dissemination (these documents) → Feedback (doc 11 iterations, revised PIRs below)`

Two collection cycles were run:

- **Cycle 1** covered the original proposal: AI-provider binary-to-generation-session attribution.
- **Cycle 2** was triggered by Cycle 1 gate failures and the tasking addendum on IP investigation. It covered proprietary-code reuse in other products. It added PIR-9 and PIR-10.
- **Cycle 3** was triggered by the tasking to use real research papers on IP tracking. It added PIR-11 (what peer-reviewed research shows about detecting proprietary code in other products, on real data) and PIR-12 (which legal frameworks govern that evidence). See doc 14.

**Collection limits.** No interviews were held, and no provider or customer was contacted. There was no access to private conversations, real malware, the founder's model, or the founder's datasets (E01). All market-demand evidence is therefore indirect.

Confidence scale: **High** means multiple independent A-grade sources agree. **Moderate** means one A-grade source or consistent B/C sources. **Low** means indirect or inferred. **Very low** means essentially no evidence.

---

## PIR-1 — Do AI providers have a recurring operational need to trace malicious code to AI-generation sessions?

| Field | Assessment |
|---|---|
| Supporting evidence | Providers repeatedly investigate malware development on their platforms (E02, E04, E05, E06). OpenAI explicitly cannot verify off-platform activity (E02), which is the gap the product targets. Publication cadence is roughly three reports per year since 2024 (E04), so the activity is recurring. |
| Contradicting evidence | Every documented case was discovered and actioned **from the on-platform side**: prompt content, account clustering, Telegram posts, Trellix overlap, embedded API keys (E02, E03, E06). None reports that an inability to match a binary to a session blocked enforcement. Providers report "no novel capability" uplift in several cases (E02, E03), which lowers the urgency of post-hoc attribution. |
| Missing evidence | How often providers receive "here is a binary, did your model write it?" requests (from law enforcement, CERTs, victims, journalists). Internal investigator time per case. Whether provider legal teams *want* this capability, given liability optics. |
| Source credibility | A (provider primary reports), with a caveat: providers choose which cases to publish (selection bias). |
| Confidence | **Low–moderate** that the need exists as a *recurring operational* need. **Moderate** that it exists as an occasional, high-salience need. |
| Collection requirements | Structured interviews with 5+ provider T&S investigators. FOIA-free proxy: count of public LE/CERT reports that name a specific AI provider as the malware's origin. |
| Product implication | Do not build the company on this need alone. At most, it is a feature inside a provider's existing stack. |

## PIR-2 — Do existing provider systems already solve it?

| Field | Assessment |
|---|---|
| Supporting evidence (that they do) | Automated classifiers plus human reviewers (E04). Cross-lab indicator sharing via FMF (E08). Generation-time code-matching infrastructure already exists at GitHub/Microsoft and AWS (E10). Providers hold the raw logs (E09). |
| Contradicting evidence | No public evidence of a *binary*→session index at any provider. OpenAI's "cannot verify off-platform" (E02) suggests the artifact-side link is not routine. |
| Missing evidence | Whether providers keep code-output fingerprints beyond the 30-day abuse-log window (E09). Whether internal tooling already does output-to-artifact matching but is unpublished. |
| Source credibility | A |
| Confidence | **Moderate** that providers have *adequate* capability for the cases they prioritize. **High** that they *could* build the missing piece in-house (I03). |
| Collection requirements | Ask providers directly: "When you receive a sample, what do you do today?" Review provider job postings for "provenance", "output fingerprinting", "attribution". |
| Product implication | A standalone vendor must offer something providers cannot easily build. The available differentiators are binary-analysis depth and cross-provider neutrality, but neutrality conflicts with providers' unwillingness to share logs (PIR-4). |

## PIR-3 — Can binary features reliably retrieve the corresponding generated source records?

| Field | Assessment |
|---|---|
| Supporting evidence | Our measured benchmark (E30): with unobfuscated synthetic programs, strings and constants survive -O0…-O3, gcc/clang, and stripping well enough for high Recall@10. See doc 09 for numbers. Literature confirms binary→source matching works at library granularity (E11, E29). |
| Contradicting evidence | The adversaries of most interest request **string encryption/obfuscation** (E05). In our benchmark, obfuscation combined with constant mutation sharply degrades recall (E30). Function-level learned matching on real code reaches only about 23% Recall@1 (E11). Optimization is the dominant confounder (E12). Malware may be generated at runtime and never written to disk (E07). Actors assemble building blocks from many sessions and multiple providers (E02, E04), so no single session holds "the source". |
| Missing evidence | Performance on **real** LLM-generated code (which is less distinctive than our synthetic corpus), on PE/Mach-O, on packed samples, and against code generated independently for different users from similar prompts. |
| Source credibility | A (literature, our own measurement), limited by the synthetic data. |
| Confidence | **Moderate** that retrieval works for naive/unobfuscated artifacts. **High** that it fails for deliberately obfuscated artifacts. |
| Collection requirements | Rerun the benchmark on real model outputs (generated under authorization from benign prompts), on Windows PE, and with UPX/commercial packers. |
| Product implication | Positioning must be "investigative lead generation for naive actors", never "attribution". Open-set rejection is mandatory. |

## PIR-4 — Can it operate without exporting private conversations or customer IP?

| Field | Assessment |
|---|---|
| Supporting evidence | Architecture A keeps keyed fingerprints inside the provider. Our slice stores only HMAC-truncated features with no plaintext (tested, E30). Investigators see only their own query plaintext plus opaque refs. |
| Contradicting evidence | Keyed hashes of **low-entropy features** (common constants, short strings) are dictionary-attackable by anyone holding the key. Fingerprints of generated code are still derived from customer content and may be "personal data / customer data" under contracts. ZDR customers' content must not be retained at all (E09), so coverage gaps are structural. An external vendor that sees neither data nor queries has little to sell besides software. |
| Missing evidence | Provider DPAs / enterprise terms on derived data. Counsel review of whether fingerprints count as "content". Cross-border constraints (EU). |
| Source credibility | A for retention facts; D for the legal interpretation (not legal advice). |
| Confidence | **Moderate** that a provider-hosted SDK *can* be privacy-acceptable. **Low** that a third-party *service* touching session data can be. |
| Collection requirements | Qualified privacy-counsel review; a provider DPO interview. |
| Product implication | Anything touching provider sessions must be on-prem software licensed to the provider, not a SaaS intelligence feed. |

## PIR-5 — Would AI providers pay an external vendor?

| Field | Assessment |
|---|---|
| Supporting evidence | Providers do buy external security tooling: Anthropic and xAI are Socket customers (E17), and OpenAI funds external defenders (E17). |
| Contradicting evidence | The buyer universe is tiny: roughly 6 FMF members plus a handful of other frontier and coding-tool vendors. They have strong in-house teams (E04, E10) and an existing sharing channel (E08). There is no public procurement signal for provenance attribution. |
| Missing evidence | Any buyer statement, budget line, RFP, or pilot. |
| Source credibility | B/C |
| Confidence | **Low** (that they would pay meaningfully for this specific capability). |
| Collection requirements | 10 provider conversations with explicit asks: pilot, test data, named budget owner. |
| Product implication | Treat providers as possible later design partners, not as the initial market. |

## PIR-6 — Is supply-chain intelligence a more attractive initial market?

| Field | Assessment |
|---|---|
| Supporting evidence | Large, proven spend: Socket at a $1B valuation with 27k orgs (E17). Many incumbents means validated demand (E18, E19). Source packages retain far more evidence than compiled binaries (E28, E30). |
| Contradicting evidence | It is crowded and fast-moving, with free tools (GuardDog) and incumbents holding 500k+ labeled malicious-package DBs (E18). A new entrant with an unvalidated classifier and no dataset in hand (E01) has no visible wedge. |
| Missing evidence | Whether "AI-generated malicious package" provenance (who or what generated it) changes any defender action. Our hypothesis is that it rarely does: defenders block a package for being malicious, not for how it was written. |
| Source credibility | B/C |
| Confidence | **High** that the market is real. **Low** that this founder can win it head-on. |
| Collection requirements | 10 interviews with AppSec / supply-chain leads asking what they would do differently with provenance. |
| Product implication | Supply chain is better as a **data source** (monitoring registries for leaked proprietary code) than as the product category. |

## PIR-7 — Do the founder's assets create a competitive advantage?

| Field | Assessment |
|---|---|
| Supporting evidence | Reverse-engineering and detection-engineering expertise is directly relevant to binary feature extraction and evidence quality (E21, E22 show these skills are what IP cases require). |
| Contradicting evidence | Neither the classifier nor the datasets exist in this repository (E01). "Detects samples with 0 VirusTotal detections" is not evidence of correctness: zero detections can mean benign. Incumbents claim 400B-file and 550k-package corpora (E18, E19). |
| Missing evidence | Model card, evaluation protocol, temporal holdout, FPR on benign software, dataset provenance and licensing. |
| Source credibility | D (founder claims, unverified) |
| Confidence | **Very low** for the assets. **Moderate** for founder expertise as a differentiator in forensic-grade evidence work. |
| Collection requirements | See the validation protocol in doc 08 §Asset validation. |
| Product implication | Do not let the roadmap depend on the classifier. Use it, if validated, as one optional signal. |

## PIR-8 — What obstacles could make the business impossible?

Summary (full list in docs 05 and 08):

1. Adversarial obfuscation defeats the evidence (E05, E30).
2. Provider data is inaccessible to third parties (E09, PIR-4).
3. Build-vs-buy favors providers building it themselves (E10).
4. Composite, multi-session, multi-provider authorship (E02, E04).
5. Liability for false accusation (E21).
6. Tiny buyer universe (PIR-5).
7. Founder assets unverified (E01).

**Confidence: moderate–high** that obstacles 1–3 together are fatal to the *original* standalone product.

---

## Cycle-2 PIRs (added after feedback loop)

## PIR-9 — Is there recurring, budgeted demand to find proprietary code inside other parties' products?

| Field | Assessment |
|---|---|
| Supporting evidence | More than 1,500 federal trade-secret filings in 2025 (record) and large damages (E23). Landmark firmware code-copying case (E22). A forensic-tool and expert-witness market already exists (E21). Leakage vectors have grown with AI tooling (E24, E25). Courts demand early identification of the trade secret (E23), which creates a pre-filing evidence need. |
| Contradicting evidence | Much trade-secret litigation is not about code. Per-company frequency is low (episodic). Buyers (law firms, experts) are services-oriented and may prefer bespoke analysis over a platform. Source-level leak monitoring is already sold (E26). |
| Missing evidence | Share of trade-secret cases involving software. Spend per case on software forensics. Whether IP owners would run continuous binary/firmware monitoring. |
| Confidence | **Moderate** that demand exists. **Low** on frequency and willingness to pay for a *product* rather than a *service*. |
| Collection requirements | 10 interviews: IP litigators, software-forensics experts, embedded/OEM IP counsel, M&A diligence. |

## PIR-10 — Is binary/package-level proprietary-code detection technically and legally feasible without receiving the IP owner's source?

| Field | Assessment |
|---|---|
| Supporting evidence | Our slice computes keyed fingerprints locally; only HMACs leave the owner's premises (E30). The IP-transplant experiment (a proprietary module embedded in another host and stripped) is measured in doc 09. |
| Contradicting evidence | Matching is only as good as the surviving features; obfuscation still defeats it (E30). Evidence admissibility requires expert explanation and exclusion of alternative explanations (E21). Acquiring third-party binaries for scanning raises licensing and anti-reverse-engineering questions (EULAs; jurisdiction-specific). |
| Confidence | **Moderate** technical. **Low–moderate** legal (needs counsel). |
| Collection requirements | Counsel opinion on lawful acquisition and analysis of third-party binaries. Expert-witness feedback on whether output would support a complaint. |

## PIR-11 — What does peer-reviewed research show about detecting proprietary code in other products, on real data?

| Field | Content |
|---|---|
| Supporting evidence | A mature field (E38, E39). A retrieve-then-verify architecture reaches 93.7% recall / 97.6% precision on real stripped C/C++ binaries, and 91.0% / 91.9% with a local open-weight model (E36). |
| Contradicting evidence | Similarity-scoring tools average < 60% recall and ≈ 75% precision on real binaries (E35). B2SFinder, the design closest to ours, reaches 19.9% / 47.9% (E36). Domain-specific code scores < 45% (E37). |
| Confidence | **High** that scoring alone is insufficient. **Moderate** that verification closes the gap for proprietary code (I08 untested). |
| Collection requirements | Revised X1 (doc 14 §8) |

## PIR-12 — Which legal frameworks govern collecting and presenting such evidence?

| Field | Content |
|---|---|
| Findings (context, not advice) | US: abstraction–filtration–comparison filters out unprotectable elements (E50 Altai). Disassembly is fair use only when fact-specific (Sega). §1201(f) covers interoperability only. EU: decompilation is permitted only for interoperability (Dir. 2009/24/EC Art. 6). Observe/study/test while running is protected (Art. 5(3); C-406/10). |
| Implication | A16 is more severe for the EU. Products need filtration-ready reports and a lawful acquisition and analysis mode chosen by counsel. |
| Confidence | Moderate (primary sources read; no counsel opinion) |
| Collection requirements | X3 counsel opinion |

## Cycle-4 PIRs (customer fixed to frontier AI labs; doc 15)

| PIR | Question | Answer after Cycle 4 | Confidence | Collection |
|---|---|---|---|---|
| PIR-13 | How do frontier labs buy outside cyber/misuse expertise? | Contractors in enforcement teams (E58), external red-teaming and evaluation organizations including SME probing (E59, E60), and expert marketplaces (E61). No evidence of buying attribution *tools*. | Moderate | X6 |
| PIR-14 | Does LLM-enabled malware create an artifact-first attribution need? | Yes. Malware calls LLM APIs at runtime with embedded keys (E51–E54). Labs check in-the-wild binaries against their own generations, in-house (E55, E57). | Moderate–high (need); low (outsourcing) | X5, X6 |
| PIR-15 | What can an outside SME sell without seeing private conversations? | Verifiable findings from public artifacts, analyst capacity under lab custody, and independent verification of public reports | Moderate | X6, counsel (A35) |
| PIR-16 | Can model-level code attribution support enforcement? | As a lead only. Strong closed-world results (E64, E65); fragile under adversarial transformation (E45, E46). | Moderate | X7 |

PIR-1 and PIR-5 are re-answered for a *services* offer in doc 15. The original no-buyer finding for a *tool* stands.

## Cycle-5 PIRs (doc 16)

| PIR | Question | Answer | Confidence |
|---|---|---|---|
| PIR-17 | Which lab budget can a malware-RE founder access at scale? | Post-training data / RL environments (E68–E70) | Moderate |
| PIR-18 | Is binary-first malware RE under-supplied as training material? | Existing sets are small evaluations (E72, E73); vendors focus on source/web vulnerabilities (E70) | Low–moderate |
| PIR-19 | Are agent/MCP security or model scanning better entries? | No; consolidated into large platforms (E77) | Moderate–high |
| PIR-20 | What can a frontier lab not get by hiring, spending or acquiring? (Cycle 6, doc 17) | Independence from itself, victim-side presence, neutrality across competitors, activities it avoids (I19) | Moderate |
| PIR-21 | Is there a mandated slot for an outside party in labs' cyber-risk process? | Yes: EU Code Appendix 3.5, Measures 3.5 and 9.2; SB 53 (E79–E83) | Moderate–high |
| PIR-22 | Who else can replicate it? | Google (lab + Mandiant + VirusTotal), IR firms, TI vendors each cover part; no provider-neutral offer found (I22, I23) | Low–moderate |
| PIR-23 | Which non-replicable moat can one founder deliver without a collection or supply network? (Cycle 7, doc 18) | Independence as an evaluator (E90, E91) | Moderate |
| PIR-24 | Where do labs need malware-RE judgement they would rather not grade themselves? | Whether an output is functional malware beyond public tools (E92, E93) | Low–moderate |

## Cycle 8

- **PIR-25:** which offer that a solo malware-RE founder can deliver has a documented, growing need and no specialist already selling it? See doc 19.
