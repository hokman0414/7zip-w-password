# 14 — Literature Review: Intellectual-Property Code Tracking (Intelligence Cycle 3)

**Scope and integrity notes**
- Every source below was located and checked against its publisher, DOI, or primary legal text during this cycle. Numbers are quoted from the papers' abstracts or result tables, not from memory.
- Legal sources are summarized as **analytical context, not legal advice**. They feed the counsel-opinion experiment (X3); they do not replace it.
- "Simulated persona" votes remain analytical perspectives, not interviews.

## 1. Intelligence cycle for this iteration

| Phase | What was done |
|---|---|
| **Direction** | New requirements: **PIR-11.** What does peer-reviewed research say about detecting proprietary code inside other products (binaries, firmware, apps, and AI models), and how well does it work on *real* data? **PIR-12.** What legal frameworks govern collecting and presenting that evidence? |
| **Collection** | Targeted searches across seven clusters, verified at the primary source: binary-to-source matching, binary code similarity, software birthmarks and plagiarism detection, authorship attribution, AI-generated-code detection and watermarking, training-data provenance, and legal frameworks. |
| **Processing** | 19 ledger entries (E32–E50) with credibility grades. Peer-reviewed venues and primary legal texts are graded A. |
| **Analysis** | ACH deltas, KAC updates, premortem updates, red team, a Round 3 persona vote, and feedback-loop iteration 7 (sections 4–8). |
| **Dissemination** | Ledger, voting matrix, decision matrix, roadmap, and executive decision updated. |
| **Feedback** | The literature contradicts our synthetic results, so X1 is redesigned around a public real-world benchmark and published baselines (section 8). |

## 2. Annotated bibliography

### 2.1 Binary-to-source matching and binary software composition analysis (closest prior art)

| ID | Source | Key verified content | Relevance |
|---|---|---|---|
| E32 | Yuan, Feng, Li, et al. **B2SFinder: Detecting Open-Source Software Reuse in COTS Software.** ASE 2019. [doi:10.1109/ASE.2019.00100](https://doi.org/10.1109/ase.2019.00100); [code](https://github.com/1dayto0day/B2SFinder) | Matches seven compilation-surviving features (strings, export/function names, constant arrays, enum arrays, string arrays, switch/case, if/else) between COTS binaries and OSS source. Uses an inverted index and Trie, with specificity- and frequency-based weighting. Evaluated on 21,991 binaries from 1,000 COTS products against 2,189 OSS projects. | **Essentially the same design as our slice**: typed string/constant/name features, inverted index, IDF-style weighting. Our matching core is *not novel*. |
| E33 | Jiang, An, Huang, et al. **BinaryAI: Binary Software Composition Analysis via Intelligent Binary Source Code Matching.** ICSE 2024. [doi:10.1145/3597503.3639100](https://doi.org/10.1145/3597503.3639100); [arXiv](https://arxiv.org/abs/2401.11161) | Decompiles stripped binaries, embeds functions with a transformer, then uses link-time locality and the call graph. Corpus of 56.3M functions from 12,013 libraries. Embedding recall@1 22.54% vs 10.75% for CodeCMR. Library detection precision 85.84% and recall 64.98%, vs 73.36% and 59.81% for Black Duck. Offered as SaaS. | State of the art for function-level binary→source matching. A commercial binary-to-source product already exists. |
| E34 | Duan, Bijlani, Xu, Kim, Lee. **Identifying Open-Source License Violation and 1-day Security Risk at Large Scale (OSSPolice).** CCS 2017. [doi:10.1145/3133956.3134048](https://doi.org/10.1145/3133956.3134048) | Hierarchical indexing of software birthmarks. Compared 1.6M Google Play apps against 60K C/C++ and 77K Java OSS sources. Found more than 40K potential GPL/AGPL violators. States it "focuses solely on the technical aspects of license compliance, not the legal issues." | Precedent for **IP-compliance detection in third-party binaries at scale**, and for separating technical flags from legal conclusions. |
| E35 | Liu, Xu, Li, et al. **Understanding the Limitations of C/C++ Binary Third-Party Library Detection Tools: An Empirical Study at Scale.** FSE 2026 (PACMSE 3, FSE089). [doi:10.1145/3808096](https://doi.org/10.1145/3808096) | Public benchmark of 38,228 cases across 1,873 libraries. Evaluates 11 academic and commercial tools: **average recall below 60%, precision about 75%**. Root causes: "binaries lose most source-code features during compilation", and libraries share features through functional similarity and dependency propagation. | **Strong contradicting evidence** to our synthetic results (E30a). Provides a public real-world benchmark for X1. |
| E36 | Liu, Xu, Zhang, Wu, Li, Liu. **Beyond Similarity Scores: Evidence-Based Third-Party Library Detection for C/C++ Binaries (BLADE).** ISSTA 2026 (PACMSE 3, ISSTA034). [doi:10.1145/3832125](https://doi.org/10.1145/3832125) | 3,403 binaries (gcc/clang, x86_64/arm, stripped). Baseline recall / precision: **B2SFinder 19.9% / 47.9%**, BAT 42.7% / 72.8%, OSSPolice 22.9% / 28.5%, BinaryAI 57.7% / 46.2%. BLADE (retrieval plus evidence verification by an LLM): 93.7% / 97.6%; 91.0% / 91.9% with an open-weight model. Removing verification costs 79.9 points of precision. Proprietary in-vehicle OTA test: recall 90.8%, precision 97.0%. Deployed in a commercial SCA product. | (a) Similarity scoring *alone* has low real-world precision. Our 0/400 false escalations are a synthetic artifact until shown otherwise. (b) The working architecture is **retrieve broadly, then verify with structured evidence**. (c) A local open-weight model keeps evidence on-premises. (d) Another commercial competitor. |
| E37 | **Empirical Study of Software Composition Analysis Tools for C/C++ Binary Programs.** IEEE Access, 2023. [doi:10.1109/ACCESS.2023.3341224](https://doi.org/10.1109/access.2023.3341224) | Black Duck, Scantist, Cybellum, and one academic tool on 16,713 binaries. Accuracy above 70% on general libraries, **below 45% on domain-specific (automotive) libraries**. False positives stayed low "due to the absence of obfuscation and the preservation of strings". | Domain-specific (proprietary-like) code is harder. Strings carry the precision. |

### 2.2 Binary code similarity (function-level clone search)

| ID | Source | Key content | Relevance |
|---|---|---|---|
| E38 | Haq & Caballero. **A Survey of Binary Code Similarity.** ACM CSUR 54(3), 2021. [doi:10.1145/3446371](https://doi.org/10.1145/3446371) | Systematizes 70 approaches (applications, characteristics, implementation, evaluation). | Shows the field is mature and gives a taxonomy for selecting baselines. |
| E39 | Marcelli, Graziano, Ugarte-Pedrero, Fratantonio, Mansouri, Balzarotti. **How Machine Learning Is Solving the Binary Function Similarity Problem.** USENIX Security 2022. [paper](https://www.usenix.org/conference/usenixsecurity22/presentation/marcelli); [code and data](https://github.com/Cisco-Talos/binary_function_similarity) | Reimplements 10 approaches on a shared cross-compiler, cross-optimization, three-architecture dataset. GNNs perform best. Fuzzy hashing works only in simple settings. Engineered features differ little from bag-of-words opcodes. | An off-the-shelf benchmark and baselines for function-level matching. Consistent with our weak opcode baseline at -O2 (E30e). |
| E40 | Ding, Fung, Charland. **Asm2Vec.** IEEE S&P 2019. [doi:10.1109/SP.2019.00003](https://doi.org/10.1109/sp.2019.00003) | Learned assembly representations, more robust to O-LLVM-style obfuscation than static features. The abstract cites "detecting patent infringements" as a use. Its stated limitations: it "cannot completely defeat code obfuscation" and has "limited interpretability". | The obfuscation-robust direction exists, but it is a black box, which is weak for **evidence**. That gap remains open. |

### 2.3 Software birthmarks, plagiarism detection, watermarking (IP-theft literature)

| ID | Source | Key content | Relevance |
|---|---|---|---|
| E41 | Luo, Ming, Wu, Liu, Zhu. **CoP: Semantics-based Obfuscation-Resilient Binary Code Similarity Comparison with Applications to Software Plagiarism Detection.** FSE 2014. [doi:10.1145/2635868.2635900](https://doi.org/10.1145/2635868.2635900) | Symbolic basic-block semantics, theorem-prover equivalence, and LCS over paths. Notes that "often the plaintiff is not allowed to access the source code of the suspicious program". | Resilient but heavyweight. Suited to **confirming** a small number of candidates, not to scanning at scale. |
| E42 | Tamada, Nakamura, Monden, Matsumoto. **Design and Evaluation of Birthmarks for Detecting Theft of Java Programs.** IASTED SE 2004 ([PDF](https://www.cc.kyoto-su.ac.jp/~tamada/publications/tamada04iasted.pdf)). Myles & Collberg. **K-gram Based Software Birthmarks.** ACM SAC 2005 ([doi:10.1145/1066677.1066753](https://doi.org/10.1145/1066677.1066753)) | Birthmarks are judged on *credibility* (distinguishing independent programs) and *resilience* (surviving transformation). Tamada et al. report 97.8% distinction and 93.4% preservation under optimizers and obfuscators on Java. | This is the evaluation vocabulary that the X1 benchmark should report, so results are comparable. |
| E43 | Schleimer, Wilkerson, Aiken. **Winnowing: Local Algorithms for Document Fingerprinting.** SIGMOD 2003. [doi:10.1145/872757.872770](https://doi.org/10.1145/872757.872770) | Guarantees detection of any shared substring of length ≥ w + k − 1. This is the algorithm behind MOSS. | Our `w:` feature is a direct implementation, so it is not novel. |
| E49 | Collberg & Thomborson. **Software Watermarking: Models and Dynamic Embeddings.** POPL 1999. [doi:10.1145/292540.292569](https://doi.org/10.1145/292540.292569) | Embeds a mark that survives translation, optimization, and obfuscation and has "a mathematical property that allows us to argue that its presence … is the result of deliberate actions". | **A proactive complement.** Owners who watermark *before* theft get far stronger evidence than any similarity score. This could be a product feature (section 6). |

### 2.4 Authorship attribution (style ≠ provenance)

| ID | Source | Key content | Relevance |
|---|---|---|---|
| E44 | Caliskan, Yamaguchi, Dauber, Harang, Rieck, Greenstadt, Narayanan. **When Coding Style Survives Compilation.** NDSS 2018. [doi:10.14722/ndss.2018.23304](https://doi.org/10.14722/ndss.2018.23304) | Binary authorship attribution reaches 96% accuracy among 100 candidates and 83% among 600 (Google Code Jam), robust to basic obfuscation and stripping. | A style signal survives compilation. It is also a programmer-privacy threat. |
| E45 | Quiring, Maier, Rieck. **Misleading Authorship Attribution of Source Code using Adversarial Learning.** USENIX Security 2019. [paper](https://www.usenix.org/conference/usenixsecurity19/presentation/quiring) | Semantics-preserving transformations drop attribution accuracy **from over 88% to 1%**, and can **impersonate**: each developer could be impersonated by 77–81% of the others on average. The authors conclude that current attribution is "inappropriate for practical application". | Empirical basis for the rule **"do not equate stylistic similarity with proven authorship."** Style evidence can be forged, so the product must not use it as proof. |

### 2.5 AI-generated code: detection, watermarking, training-data provenance

| ID | Source | Key content | Relevance |
|---|---|---|---|
| E46 | Pordanesh, Bukhari, Tan, De Carli. **Hiding in Plain Sight: On the Robustness of AI-generated Code Detection.** DIMVA 2025 ([PDF](https://ldklab.github.io/assets/papers/dimva25-aicode.pdf)). **Assessing AI Detectors in Identifying AI-Generated Code.** ICSE-SEET 2024 ([doi:10.1145/3639474.3640068](https://doi.org/10.1145/3639474.3640068)). **An Empirical Study to Evaluate AIGC Detectors on Code Content.** ASE 2024 ([doi:10.1145/3691620.3695468](https://doi.org/10.1145/3691620.3695468)) | Detectors are "fragile" and fail across training-set and prompt changes. GPTZero and the GPT-2 detector score about 0.5 accuracy on code. Thirteen detectors perform worse on code than on natural language. | Further disconfirms H1. If "AI or human?" is unreliable, "which AI *session*?" from an artifact is far harder. |
| E47 | Lee, Hong, Ahn, et al. **Who Wrote this Code? Watermarking for Code Generation (SWEET).** ACL 2024. [ACL Anthology](https://aclanthology.org/2024.acl-long.268/) | Standard LLM watermarks fail on low-entropy code. SWEET watermarks only high-entropy tokens. | AI-code provenance is feasible **only at generation time, by the provider**. That supports H3 and H5: a third-party vendor cannot add it after the fact. |
| E48 | Sun, Du, Song, Ni, Li. **CoProtector.** WWW 2022 ([doi:10.1145/3485447.3512225](https://doi.org/10.1145/3485447.3512225)). Yang et al. **Gotcha! This Model Uses My Code!** IEEE TSE 2024 ([doi:10.1109/TSE.2024.3482719](https://doi.org/10.1109/tse.2024.3482719)) | CoProtector: owners plant watermark backdoors in their repos, then audit a suspect model with a t-test. Gotcha: membership inference on code-completion models reaches TPR 0.95 at **FPR 0.10**, using a surrogate model and partial training-data knowledge. | Shows a *different* "proprietary code used in another product" channel: **use as training data**. A 10% false-positive rate is unusable as evidence. Watermarking works only if applied before training. Recorded as candidate G. |

### 2.6 Legal frameworks (primary sources; context for X3, not advice)

| ID | Source | Key content | Implication |
|---|---|---|---|
| E50a | *Computer Associates v. Altai*, 982 F.2d 693 (2d Cir. 1992). [Justia](https://law.justia.com/cases/federal/appellate-courts/F2/982/693/137252/) | The abstraction–filtration–comparison test. Elements dictated by efficiency, external factors, or the public domain are **filtered out** before comparison. | A match on unprotectable elements (common strings, standard constants, protocol values) is not evidence of copying. Reports must support **filtration**, for example by suppressing features found in public or OSS corpora. |
| E50b | *Sega v. Accolade*, 977 F.2d 1510 (9th Cir. 1992). [Justia](https://law.justia.com/cases/federal/appellate-courts/F2/977/1510/305345/) | Disassembly is fair use "when the person seeking the understanding has a legitimate reason for doing so and when no other means of access … exists". | The US fair-use route is fact-specific. It was decided for interoperability; its application to infringement *detection* needs counsel. |
| E50c | 17 U.S.C. §1201(f) (via [Digital Law Online](https://digital-law-online.info/lpdi1.0/treatise48.html)) | Anti-circumvention exemption limited to **interoperability** analysis by a lawful user. | Encrypted or locked firmware may raise §1201 issues that this exemption does not obviously cover. |
| E50d | EU Directive 2009/24/EC, Arts. 5(3) and 6. [EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX%3A32009L0024) | Art. 5(3): a lawful user may "observe, study or test the functioning" while loading or running. Art. 6: decompilation only where "indispensable" for **interoperability**, and the results may not be used for other goals. | Static decompilation of a competitor's binary **for infringement detection** is not clearly within Art. 6. **A16 becomes more severe for the EU.** |
| E50e | CJEU C-406/10 (SAS Institute), [ECLI:EU:C:2012:259](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX%3A62010CJ0406) | The Art. 5(3) observe/study/test right cannot be excluded by licence. | Running a lawfully acquired product and observing its behaviour may be safer than static decompilation. This is a design option to put to counsel. |

## 3. Key findings

1. **Our core method is established prior art.** B2SFinder (2019) uses the same feature family with the same weighting idea. BAT (2011) and OSSPolice (2017) predate it. Winnowing is MOSS. *Differentiation cannot rest on the algorithm.* (E32, E34, E43, plus E29)
2. **Real-world performance is far below our synthetic numbers.** On independent real benchmarks, feature-matching tools reach about 20–60% recall with 28–79% precision (E35, E36). Domain-specific code scores below 45% (E37). Our R@10 = 1.0 and 0/400 false escalations (E30) must be treated as an **upper bound from an easy, synthetic distribution**.
3. **The architecture that works on real data is "retrieve, then verify with evidence"** (E36: verification adds about 80 points of precision). That is also exactly what an evidence product needs. A local open-weight model gets within about 3–6 points of GPT-5 (E36), which is compatible with owner custody.
4. **Proprietary-code detection differs from OSS library detection in a way that may help.** This is an **inference (I08), not tested.** Much of the measured failure comes from overlap *between* libraries (forks, shared dependencies; E35). A single owner's proprietary code, after suppressing known-OSS features, may overlap less. It may also overlap *more*, if proprietary code embeds OSS. X1 must measure this.
5. **Style is not evidence.** Attribution survives compilation (E44) but can be defeated and forged (E45). The product must keep stylometry out of its evidence chain.
6. **AI-session provenance cannot be done after the fact.** Detectors are fragile (E46). Robust provenance requires provider-side generation-time watermarking (E47). This further confirms the decision to drop the original concept.
7. **The legal envelope is narrower than assumed, especially in the EU** (E50d). Courts filter unprotectable elements (E50a), which turns into a concrete product requirement: OSS and boilerplate feature suppression, plus filtration-ready reports.
8. **Proactive watermarking (E49) is the strongest evidence class.** Pairing passive fingerprint search with optional owner-side watermarking would give a "deliberate act" signal that similarity cannot.

## 4. ACH deltas (doc 04)

| Hypothesis | New evidence | Direction | Updated assessment |
|---|---|---|---|
| H1 Unmet provider need (third-party session attribution) | E46, E47 | ↓ | Remains least likely. Provenance lives at generation time inside providers. |
| H3 Interesting, not commercially important | E47 | ↑ | Strengthened for the original concept. |
| H6 Binary→source too unreliable | E35, E36, E37 | ↑ (major) | **No longer only "conditionally rejected".** Real-data results support H6 for similarity scoring *alone*. E36 shows verification overcomes much of the gap, so H6 holds for scoring-only designs and is weakened for retrieve-and-verify designs. |
| H8 IP-owner detection in compiled products | E32–E34 (prior art), E35–E37 (difficulty), E36 (a working architecture), E50 (legal) | ↓ differentiation; ↔ need; ↑ path to feasibility | Still the most promising direction, but with **lower defensibility** and a **harder legal envelope**. Its key uncertainty is now *technical on real data* as well as commercial. |

## 5. Key-assumption updates (doc 05)

| ID | Assumption | Previous | Updated | Evidence |
|---|---|---|---|---|
| A16 | Lawful acquisition and analysis of third-party binaries is feasible | Untested, critical | **Doubtful in the EU for static decompilation; fact-specific in the US.** Still critical. | E50b–E50e |
| A19 | Incumbents will not add compiled-artifact matching quickly | Untested | **Fails.** Black Duck, Cybellum, Scantist, BinaryAI, and a BLADE-based product already do binary→source matching for OSS. Pointing them at a customer's proprietary corpus is an incremental feature. | E33, E36, E37 |
| A20 | The method is novel enough to defend | Fails (algorithmic) | **Fails more strongly** (B2SFinder is near-identical) | E32 |
| A23 | Watermarking will not make the product obsolete | Holds for now | Holds for *passive* detection of unwatermarked legacy code. Watermarking is better seen as a complement. | E47, E49 |
| A25 (new) | Synthetic benchmark results transfer to real binaries | Implicit | **Fails as stated.** Real-world tools reach 20–60% recall. | E35–E37 |
| A26 (new) | Proprietary code is more distinctive than OSS libraries after OSS-feature suppression | — | **Untested (I08).** Gating for X1. | E35 (overlap root cause) |
| A27 (new) | Evidence can be verified locally without sending code to external AI services | — | **Plausible.** An open-weight model reaches 91–92% (E36). Must be re-measured on our data. | E36 |
| A28 (new) | Stylometric signals can support provenance claims | — | **Rejected as evidence.** Forgeable. | E45 |

## 6. Red team: the strongest case against continuing F

> "BLADE-class tools are already deployed commercially and reach about 94% on real binaries. Indexing one more corpus, the customer's own code, is configuration, not a company. Your 'owner-custodied' angle is a deployment option any vendor can offer. In the EU you may not even be allowed to decompile the suspect product for this purpose. And the published baselines that look like your prototype score about 20% recall in the wild."

**Rebuttal (partial).**
- The deployed tools target *OSS library identification for vulnerabilities and licences*. None was found that is positioned as **proprietary-code infringement evidence**. Infringement evidence needs filtration support (E50a), chain of custody, reproducible exhibits, and expert review.
- That is a workflow and evidence product, not an algorithm. Whether buyers pay for that workflow is still X2.
- The red-team point on algorithmic novelty is **accepted**.

## 7. Persona Round 3 (literature-informed; simulated)

The full 8-dimension table is in doc 07, Round 3. Below are the personas whose overall vote or key sub-score moved most. Most other personas lowered Technical feasibility (4→3) and Defensibility (3→2) on E35 and E32/E33 without changing their overall vote.

| # | Persona | Round 2 Ovr | **Round 3 Ovr** | Evidence for change | Would change vote if… |
|---|---|---|---|---|---|
| 4 | Malware RE | 4 | **3** | Prior art is near-identical (E32). Real-world recall of feature matching is about 20% for B2SFinder (E36). | X1 shows ≥ 0.8 recall with verification on real proprietary-like code |
| 5 | ML Scientist | 3 | **3** (Tech 4→3) | A25 fails. Our false-escalation result is synthetic (E35, E36). | Evaluation on the FSE 2026 public benchmark plus a proprietary-like split |
| 8 | Forensics Investigator | 4 | **4** | Retrieve-then-verify (E36) and filtration (E50a) map directly onto an expert workflow. Its value is in evidence packaging, not in the match score. | An expert rejects a sample packet |
| 9 | Privacy Counsel | 3 | **2** (Priv 3→2) | EU Art. 6 limits decompilation to interoperability (E50d). §1201(f) has the same scope (E50c). | A counsel opinion identifies a lawful mode, for example Art. 5(3) observe/run, or customer-owned artifacts |
| 12 | Skeptical VC | 3 | **2** (Def 2→1) | Incumbents and deployed binary SCA products (E33, E36, E37). A19 fails. | Paid demand for the *evidence workflow* specifically (X2) |

**F after Round 3:** Ovr scores are 3, 3, 3, 3, 3, 3, 3, 4, 2, 3, 3, 2. **Median 3; 1/12 at ≥ 4.** The consensus gate is not met. The critical legal blocker (A16) is unresolved and more severe.

**New candidate G (training-data provenance audit: "was my proprietary code used to train model X?"),** assessed once:

- **Need:** real. Code models are trained on confidential company code (E48 Gotcha introduction; E24, E25).
- **Technology is not evidence-grade:**
  - membership inference has FPR 0.10 and needs a surrogate model plus partial training-data knowledge (E48);
  - dataset watermarking works only if applied *before* training (E48).
- **No founder RE advantage.**

Persona Ovr medians: Imp 3, Tech 2, Dem U, Def 2, Priv 2, Fdr 1, Adopt 2, **Ovr 2; 0/12 at ≥ 4.** G is **not pursued**. Monitor it as a signpost: a membership-inference method with FPR ≤ 1% would reopen G.

## 8. Feedback loop iteration 7 and what changed

| Field | Content |
|---|---|
| Candidate | F (IP code-reuse investigation) |
| Highest-impact objection | "The method is prior art, and it does not work on real binaries." |
| Type | Evidence gap (real-data performance) **and** competitive flaw (novelty) |
| Falsifiable test | Literature: does peer-reviewed real-world evaluation of binary→source feature matching show recall ≥ 0.8 and precision ≥ 0.9? |
| Evidence | E32–E37 |
| Result | **Falsified for similarity scoring alone** (recall 20–60%, precision 28–79%). **Supported for retrieve-then-verify** (93.7% / 97.6%; 91% / 92% with a local model). |
| What changed | 1. The **architecture** changes: add a verification stage with evidence collection (identity markers, OSS-feature suppression, cross-feature consistency), run locally. 2. **X1** is redesigned (below). 3. **F's status moves from PILOT FIRST to RESEARCH FIRST.** The technical hypothesis is unproven on real data, so customer pilots would be premature. Buyer discovery (X2) and the counsel opinion (X3) continue in parallel because they are cheap and independent. 4. **The product claim narrows** to an evidence workflow (filtration-ready, reproducible, expert-reviewed), not a novel matching algorithm. 5. **An optional proactive watermark module** is added to the backlog (E49). |

### Revised X1 (replaces doc 09 next experiment X1)

| Element | Specification |
|---|---|
| Datasets | (a) the FSE 2026 public benchmark (E35), for comparability; (b) a **proprietary-like split**: real OSS functions transplanted into unrelated real hosts, stripped, cross-architecture (x86_64/ARM), with known-OSS feature suppression |
| Baselines | B2SFinder (open source, E32), BAT/BANG (E29), our scoring-only slice, our slice plus local verification |
| Metrics | Recall and precision at the component level and function level; birthmark *credibility* and *resilience* (E42); false-escalation rate on out-of-index binaries |
| Pass | Retrieve-and-verify reaches **recall ≥ 0.80 and precision ≥ 0.95** on the proprietary-like split, with a local model only (no external AI service) |
| Kill | Precision < 0.90 after verification, or recall < 0.60. F then becomes a services-only offer. |
