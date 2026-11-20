# 02 — Evidence Ledger

Living ledger. Every claim in the other documents cites an `E-` identifier from this file. Research was performed on 2026-11-20 with live web access; sources were read at that date.

**Credibility scale.** A = primary/official source or peer-reviewed paper. B = reputable secondary reporting or court record summary. C = vendor marketing / self-reported claim. D = unverified or inferred.

**Type.** F = fact (directly observed or documented), I = inference by this team, H = hypothesis to be tested.

**What is *not* in this ledger.** No customer interviews were conducted. No AI provider was contacted. No real malware, real AI conversation, or proprietary code was used. Persona assessments (doc 06) are simulated analytical perspectives and are **not** evidence; they are never cited as `E-` entries.

| ID | Evidence | Source | Cred. | Type | Bears on |
|---|---|---|---|---|---|
| E01 | The repository (`main` and all 15 remote branches) contains **no malware classifier, model weights, training code, inference interface, or supply-chain package dataset**. `main` held only a one-line README. Other branches contain unrelated projects (stock research, influence research, conference-talk scraping). | Direct inspection (`git ls-tree -r` on every branch) | A | F | PIR-7, Phase 6, Phase 12 |
| E02 | OpenAI (Oct 2025) banned accounts of Russian-speaking criminal actors developing RATs, credential stealers, loaders. Model refused direct malicious requests; actors elicited **building-block code** and assembled it off-platform. OpenAI states it is "not able to independently verify any off-platform activity" and "shared relevant indicators with industry partners". | [OpenAI report PDF](https://cdn.openai.com/threat-intelligence-reports/7d662b68-952f-4dfd-a2f2-fe55b041cc4a/disrupting-malicious-uses-of-ai-october-2025.pdf); [case page](https://openai.com/index/disrupting-malicious-uses-of-ai-russian-speaking-malware-tooling/) | A | F | PIR-1, PIR-2, PIR-3 |
| E03 | OpenAI linked a Korean-language account cluster to external reporting (Trellix: XenoRAT, GitHub-based C2) through **indicator and thematic overlap**, not through artifact-to-session code matching. | [OpenAI case page](https://openai.com/index/disrupting-malicious-uses-of-ai-korean-language-malware-support/) | A | F | PIR-1, PIR-2 |
| E04 | OpenAI has published threat reports since Feb 2024 (≥ 9 editions through June 2026); detection uses "automated systems" plus "human reviewers". Feb 2026 report notes actors use **different AI models at different workflow points**. | [OpenAI index](https://openai.com/index/disrupting-malicious-uses-of-ai/); [Feb 2026](https://openai.com/index/disrupting-malicious-ai-uses/) | A | F | PIR-1, PIR-2, PIR-8 |
| E05 | Anthropic (Aug 2025): GTG-2002 used Claude Code for extortion against ≥17 orgs, including malware with **string encryption, anti-debugging, filename masquerading**; GTG-5004 built and sold ransomware-as-a-service with Claude. | [Anthropic threat report PDF](https://www-cdn.anthropic.com/b2a76c6f6992465c09a6f2fce282f6c0cea8c200.pdf); [BleepingComputer](https://www.bleepingcomputer.com/news/security/malware-devs-abuse-anthropics-claude-ai-to-build-ransomware/) | A | F | PIR-1, PIR-3 |
| E06 | Google GTIG (Nov 2025): PROMPTFLUX / PROMPTSTEAL call LLM APIs **at runtime** with hard-coded keys; Google "disabled the assets". Attribution path ran via embedded API keys, not via code similarity. | [GTIG blog](https://cloud.google.com/blog/topics/threat-intelligence/threat-actor-usage-of-ai-tools) | A | F | PIR-1, PIR-2 |
| E07 | GTIG (late 2025): HONESTCUE asks Gemini for C# source and compiles it **in memory**; no payload artifact on disk. | [GTIG blog](https://cloud.google.com/blog/topics/threat-intelligence/distillation-experimentation-integration-ai-adversarial-use) | A | F | PIR-3 |
| E08 | Frontier Model Forum info-sharing agreement (Mar 2025), signed by all members (Anthropic, Amazon, Google DeepMind, Meta, Microsoft, OpenAI); covers threat actors, attack vectors, and cyber-threat indicators. Restricted to members. | [FMF announcement](https://www.frontiermodelforum.org/updates/fmf-announces-first-of-its-kind-information-sharing-agreement/); [issue brief](https://www.frontiermodelforum.org/issue-briefs/information-sharing-incident-reporting-and-incident-response-for-frontier-ai-risks/) | A | F | PIR-2, PIR-5 |
| E09 | OpenAI API abuse-monitoring logs (prompts, responses) are retained **up to 30 days** by default; approved customers may enable Zero Data Retention or Modified Abuse Monitoring. | [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data) | A | F | PIR-4, PIR-8 |
| E10 | GitHub Copilot **already runs generation-time code matching** (suggestion plus about 150 chars of context against a public-code index refreshed every few months). Amazon Q keeps a code-reference log. | [GitHub docs](https://github.com/github/docs/blob/main/content/copilot/concepts/completions/code-referencing.md); [AWS docs](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/code-reference.html) | A | F | PIR-2, H5 |
| E11 | BinaryAI (ICSE 2024): function-level binary→source embedding **Recall@1 22.7%, Recall@100 70.5%**; with link-time locality Recall@1 66.9%. TPL detection precision 85.8% / recall 65.0% vs Black Duck 73.4% / 59.8%. | [arXiv 2401.11161](https://arxiv.org/abs/2401.11161) | A | F | PIR-3, H6 |
| E12 | BinKit / TikNib (IEEE TSE 2022): **optimization level is the most influential factor** in binary similarity, exceeding architecture differences. | [arXiv 2011.10749](https://arxiv.org/abs/2011.10749) | A | F | PIR-3 |
| E13 | Code watermark robustness is weak: SWEET AUROC drops to about 0.8 after renaming all variables; obfuscation drives n-gram code watermarks to around 0.5 AUROC (coin-flip). | [SWEET](https://arxiv.org/abs/2305.15060); [Disappearing Ink](https://arxiv.org/html/2507.05512); [LNET 2025](https://doi.org/10.1109/lnet.2025.3616325) | A | F | Phase 4 cat. 10, H6 |
| E14 | Commercial AI-code detectors claim ≥ 95% accuracy (Sigrid, Span). Independent benchmarks (RealAIGC at ASE 2026, AICD Bench 2026) find **no method generalizes**, and all perform poorly at commit/PR level and on hybrid code. | [Sigrid docs](https://docs.sigrid-says.com/capabilities/faq-ai-code-governance.html); [AICD Bench](https://arxiv.org/html/2602.02079); [RealAIGC](https://dlnext.acm.org/doi/10.1145/3832783.3834411) | A (papers) / C (vendor) | F | Phase 4 cat. 2 |
| E15 | Black Duck sells snippet analysis for AI-generated code (≈2 s per 20–50-line block) and Binary Analysis for components in compiled artifacts, matched against an **open-source** KnowledgeBase. | [Black Duck blog](https://www.blackduck.com/blog/analyze-ai-generated-code-black-duck-snippet-api.html); [Binary Analysis](https://www.blackduck.com/software-composition-analysis-tools/binary-analysis.html) | C | F | Phase 4 cat. 1, 9 |
| E16 | FOSSA + SCANOSS (Jan 2026) snippet scanning for AI code IP risk; winnowing fingerprints; FOSSA stores fingerprints permanently and matched source for 30 days. SCANOSS cites Software Transparency Foundation: 1–5% of LLM code is highly similar to open source. | [FOSSA docs](https://docs.fossa.com/docs/cli/features/snippet-scanning); [SCANOSS](https://scanoss.com/post/fossa-partners-with-scanoss-to-help-organisations-manage-ai-coding-risks/) | C | F | Phase 4 cat. 1, 9 |
| E17 | Socket: $60M Series C at $1B valuation (May 2026); >27,000 orgs; customers include **Anthropic, xAI, Cursor, Replit**; flagged the Axios compromise within 6 minutes. | [Socket Series C](https://socket.dev/blog/series-c); [SecurityWeek](https://www.securityweek.com/socket-raises-60-million-at-1-billion-valuation/) | C (B for funding) | F | PIR-6, H4 |
| E18 | Malicious-package detection is crowded: Veracode acquired Phylum (Jan 2025, nearly 500k malicious packages identified); Checkmarx claims 550k+ malicious-package DB; JFrog Xray scores every new npm/PyPI/NuGet/Maven package; Datadog GuardDog is free/open source. | [Veracode](https://www.veracode.com/blog/innovating-secure-software-supply-chains-veracode-acquires-phylum/); [Checkmarx](https://checkmarx.com/product/malicious-packages/); [JFrog](https://docs.jfrog.com/security/docs/malicious-package-detection); [GuardDog](https://github.com/datadog/guarddog/) | A/C | F | PIR-6, PIR-7 |
| E19 | ReversingLabs Spectra Assure: static "complex binary analysis" of whole software packages; claims a 400B-file threat DB and 16 proprietary engines. | [RL docs](https://docs.secure.software/concepts/spectra-assure-analysis) | C | F | PIR-6, PIR-7 |
| E20 | Intezer "genetic" code-reuse analysis links malware variants via shared code genes (e.g., WannaCry ↔ Lazarus). | [Intezer](https://intezer.com/blog/what-is-genetic-malware-analysis) | C | F | Phase 4 cat. 3, 7 |
| E21 | SAFE Corp CodeSuite (CodeMatch, BitMatch, etc.) is a commercial software-forensics suite used by expert witnesses. Its whitepaper lists **alternative explanations for correlation**: third-party code, code generators, common identifiers, common algorithms, common author. | [CodeMatch](https://www.safe-corp.com/products_codematch.htm); [whitepaper](https://www.safe-corp.com/documents/CodeMatch_Whitepaper.pdf) | C/B | F | Phase 4 IP, PIR-8 |
| E22 | *Motorola v. Hytera*: jury found Motorola source code copied into Hytera radio **firmware**; misspellings reproduced; functions renamed to conceal; $345.8M compensatory + $418.8M punitive. A 2025 contempt ruling found the "redesigned" H-Series substantially the same. | [Kirkland](https://www.kirkland.com/news/in-the-news/2020/03/kirkland-turns-logistics-nightmare-into-motorola); [N.D. Ill. 2025](https://law.justia.com/cases/federal/district-courts/illinois/ilndce/1:2017cv01973/337681/1905/) | B | F | IP pivot |
| E23 | Lex Machina 2026: **> 1,500 federal trade-secret filings in 2025** (record, about +20% YoY). Juries awarded $716M actual + $510M punitive (2023–25). Courts increasingly require early identification of the trade secret. | [LexisNexis release](https://www.lexisnexis.com/news/en/lex-machina-2026-trade-secret-litigation-report-federal-trade-secret-filings-hit-an-all-time-high-in-2025); [Reuters](https://www.reuters.com/legal/legalindustry/examining-employee-mobility-remote-work-ai-trade-secret-litigation-surges--pracin-2026-02-23/) | B | F | IP pivot, PIR-5 |
| E24 | Lasso "Wayback Copilot": content of 20,580 since-private GitHub repos (16,290 orgs) was retrievable through Copilot/Bing cache. | [Lasso](https://www.lasso.security/blog/lasso-major-vulnerability-in-microsoft-copilot); [TechCrunch](https://techcrunch.com/2025/02/26/thousands-of-exposed-github-repositories-now-private-can-still-be-accessed-through-copilot/) | B | F | IP pivot |
| E25 | Code LLMs memorize and can disclose training snippets. Commercial AI code generators produced Type-1/2 clones at up to 7.5% (ACM PACMSE 2025). | [PACMSE](https://dl.acm.org/doi/10.1145/3729397); [arXiv 2503.22760](https://arxiv.org/abs/2503.22760) | A | F | IP pivot, H3 |
| E26 | **Source-level proprietary-code leak monitoring already exists**: GitGuardian (public GitHub), Cycode (fingerprinting + public repo scanning), BigID (fingerprinting, "even if refactored"), Verasity (GitHub/GitLab/npm/PyPI). | [GitGuardian](https://blog.gitguardian.com/pr_code_security_platform_announcement/); [Cycode](https://cycode.com/source-code-leakage-detection/); [BigID](https://bigid.com/blog/bigid-source-code-protection/); [Verasity](https://verasity.ai/use-cases/developer-ecosystem-monitoring) | C | F | IP pivot differentiation |
| E27 | Coding-agent provenance/governance is crowded and well funded: Entire ($60M seed; "Checkpoints"), Bitloops, RootBlocks (signed receipts), Hunaru, Backslash (Series A). | [GeekWire](https://www.geekwire.com/2026/former-github-ceo-launches-new-developer-platform-with-huge-60m-seed-round/); [Bitloops](https://bitloops.com/blog/we-raised-to-build-git-for-ai-coding); [RootBlocks](https://rootblocks.com/); [Backslash](https://firstraysvc.com/news/backslash-series-a) | C/B | F | Candidate D |
| E28 | HP Wolf (Sep 2024): AI-generated malicious VBScript/JS identified from comments and structure. Analysts note that **without the comments it would be almost impossible** to tell. | [HP report](https://threatresearch.ext.hp.com/wp-content/uploads/2024/09/HP_Wolf_Security_Threat_Insights_Report_September_2024.pdf); [SecurityWeek](https://www.securityweek.com/ai-generated-malware-found-in-the-wild/) | A/B | F | PIR-3, H7 |
| E29 | String-literal and constant matching from binaries to a source corpus is **established prior art**: BAT (MSR 2011) and BANG, used in GPL enforcement. | [BAT paper](https://edolstra.github.io/pubs/clones-msr2011-final.pdf); [BANG](https://github.com/armijnhemel/binaryanalysis-ng) | A | F | Novelty red team |
| E30 | Our benchmark (synthetic benign C, gcc 13 / clang 18, 10,000-record index). See `09_benchmark_design.md` and `bench/results/`. Synthetic data only, so external validity is limited. | Measured in this repo | A (for what it measures) | F | PIR-3, H6 |
| E30a | Naive builds: hybrid R@10 = 1.000 for gcc-O0, gcc-O2, gcc-O3-stripped, and clang-O2; 0.999 for clang-Os-stripped. Escalation recall 0.991 on gcc-O3-stripped. | `bench/results/default/results.md` | A | F | H6 |
| E30b | Adversarial: string obfuscation plus constant mutation drops R@10 to 0.768 and escalation recall to 0.200. In the boilerplate-heavy corpus it falls to 0.348 and 0.010. | same; `bench/results/boilerplate_heavy/` | A | F | H2, H7 |
| E30c | Open set: 0 of 400 held-out out-of-index binaries escalated, and 0 wrong-candidate escalations, in both corpora. | same | A | F | PIR-3 |
| E30d | IP transplant (2 functions renamed into a new host, stripped -O2): R@10 = 1.000 (R@1 0.845), escalation 0.88. The boilerplate-heavy corpus gives R@10 0.66 and escalation 0.135. | same | A | F | H8 |
| E30e | Baselines: opcode 5-gram binary similarity R@10 = 0.583 at O0 and 0.034 at O2. Exact-string match fails under obfuscation (0.329). Cost: about 1.5 KB and 116 features per record; search 0.28 ms median; extraction 4.5 ms median. | same | A | F | PIR-3, PIR-6 |
| E31 | GitHub Copilot index covers public GitHub only, is refreshed every few months, and does not check user-edited suggestions. A "no match" means "not in this index under this mechanism". | [GitHub docs](https://github.com/github/docs/blob/main/content/copilot/concepts/completions/code-referencing.md); [analysis](https://oleg.is/blog/handle-copilot-public-code-matches) | A/D | F | PIR-3 (coverage gaps) |
| E32 | B2SFinder (ASE 2019): binary→source OSS-reuse detection using strings, names, constant arrays, and switch/if structures. Uses an inverted index and specificity weighting. **Near-identical to our slice's design.** | [doi:10.1109/ASE.2019.00100](https://doi.org/10.1109/ase.2019.00100) | A | F | Novelty (A20) |
| E33 | BinaryAI (ICSE 2024): transformer function embeddings plus link-time locality. Library-detection precision/recall 85.84/64.98% vs Black Duck 73.36/59.81%. Offered as SaaS. | [doi:10.1145/3597503.3639100](https://doi.org/10.1145/3597503.3639100) | A | F | Competition, feasibility |
| E34 | OSSPolice (CCS 2017): 1.6M apps vs 137K OSS sources; > 40K potential GPL/AGPL violators. Technical flags only, "not the legal issues". | [doi:10.1145/3133956.3134048](https://doi.org/10.1145/3133956.3134048) | A | F | IP-compliance precedent |
| E35 | FSE 2026 study: 11 binary TPL tools on 38,228 cases. **Average recall < 60%, precision ≈ 75%.** Compilation removes most source features; library features overlap. | [doi:10.1145/3808096](https://doi.org/10.1145/3808096) | A | F | **Contradicts E30a** (A25) |
| E36 | BLADE (ISSTA 2026): baselines (recall/precision) B2SFinder 19.9/47.9, BAT 42.7/72.8, OSSPolice 22.9/28.5, BinaryAI 57.7/46.2. Retrieve-then-LLM-verify reaches 93.7/97.6; open-weight model 91.0/91.9; proprietary OTA test 90.8/97.0. Verification adds about 80 points of precision. Commercially deployed. | [doi:10.1145/3832125](https://doi.org/10.1145/3832125) | A | F | Feasibility path, competition |
| E37 | IEEE Access 2023: binary SCA tools > 70% accuracy on general libraries, **< 45% on domain-specific (automotive)**. Low false positives attributed to unobfuscated, string-preserving binaries. | [doi:10.1109/ACCESS.2023.3341224](https://doi.org/10.1109/access.2023.3341224) | B | F | A26 |
| E38 | Haq & Caballero, binary code similarity survey (70 approaches), ACM CSUR 2021 | [doi:10.1145/3446371](https://doi.org/10.1145/3446371) | A | F | Baseline selection |
| E39 | Marcelli et al., USENIX Sec 2022: 10 reimplemented approaches; GNNs best; fuzzy hashing works only in simple settings. Dataset is public. | [USENIX](https://www.usenix.org/conference/usenixsecurity22/presentation/marcelli) | A | F | Benchmarking |
| E40 | Asm2Vec (S&P 2019): more obfuscation-robust learned representations. Authors note it "cannot completely defeat code obfuscation" and has "limited interpretability". | [doi:10.1109/SP.2019.00003](https://doi.org/10.1109/sp.2019.00003) | A | F | H2/H6, evidence explainability |
| E41 | CoP (FSE 2014): obfuscation-resilient semantic binary plagiarism detection (symbolic execution + LCS). Heavyweight. | [doi:10.1145/2635868.2635900](https://doi.org/10.1145/2635868.2635900) | A | F | Confirmation stage |
| E42 | Software birthmarks: Tamada et al. 2004 (97.8% distinction, 93.4% preservation, Java); Myles & Collberg SAC 2005 (k-gram birthmarks; credibility and resilience criteria). | [PDF](https://www.cc.kyoto-su.ac.jp/~tamada/publications/tamada04iasted.pdf); [doi:10.1145/1066677.1066753](https://doi.org/10.1145/1066677.1066753) | A | F | Evaluation vocabulary |
| E43 | Winnowing (SIGMOD 2003), the MOSS algorithm: guaranteed detection of shared substrings ≥ w + k − 1 | [doi:10.1145/872757.872770](https://doi.org/10.1145/872757.872770) | A | F | Novelty (A20) |
| E44 | Caliskan et al. (NDSS 2018): binary authorship attribution at 96% (100 authors) and 83% (600 authors); survives stripping and basic obfuscation | [doi:10.14722/ndss.2018.23304](https://doi.org/10.14722/ndss.2018.23304) | A | F | Style signal, privacy |
| E45 | Quiring et al. (USENIX Sec 2019): adversarial transformations drop source attribution from > 88% to 1% and enable impersonation | [USENIX](https://www.usenix.org/conference/usenixsecurity19/presentation/quiring) | A | F | A28: style ≠ authorship |
| E46 | AI-generated-code detectors are fragile: DIMVA 2025 (Pordanesh et al.); ICSE-SEET 2024 (about 0.5 accuracy for GPTZero/GPT-2 detector); ASE 2024 (13 detectors, worse on code) | [DIMVA PDF](https://ldklab.github.io/assets/papers/dimva25-aicode.pdf); [doi:10.1145/3639474.3640068](https://doi.org/10.1145/3639474.3640068); [doi:10.1145/3691620.3695468](https://doi.org/10.1145/3691620.3695468) | A | F | H1 |
| E47 | SWEET (ACL 2024): standard LLM watermarks fail on low-entropy code; entropy-thresholded watermarking needed. Generation-time, provider-side. | [ACL Anthology](https://aclanthology.org/2024.acl-long.268/) | A | F | H3/H5 |
| E48 | Training-data provenance: CoProtector (WWW 2022, pre-training repo watermarks + t-test audit); Gotcha (TSE 2024, membership inference TPR 0.95 / **FPR 0.10**) | [doi:10.1145/3485447.3512225](https://doi.org/10.1145/3485447.3512225); [doi:10.1109/TSE.2024.3482719](https://doi.org/10.1109/tse.2024.3482719) | A | F | Candidate G |
| E49 | Collberg & Thomborson (POPL 1999): software watermarking, robust to transformation, with a mark that evidences deliberate action | [doi:10.1145/292540.292569](https://doi.org/10.1145/292540.292569) | A | F | Proactive evidence |
| E50 | Legal primary sources: *CA v. Altai* (AFC filtration); *Sega v. Accolade* (disassembly fair use, fact-specific); 17 U.S.C. §1201(f) (interoperability only); EU Dir. 2009/24/EC Arts. 5(3) and 6 (decompilation only for interoperability); CJEU C-406/10. **Context only; not legal advice.** | [Altai](https://law.justia.com/cases/federal/appellate-courts/F2/982/693/137252/); [Sega](https://law.justia.com/cases/federal/appellate-courts/F2/977/1510/305345/); [EUR-Lex 2009/24](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX%3A32009L0024); [C-406/10](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX%3A62010CJ0406) | A | F | A16, PIR-12 |

## Inferences derived from the ledger (type I)

| ID | Inference | Basis | Confidence |
|---|---|---|---|
| I01 | Providers can already attribute malware-development activity to accounts **from the on-platform side** (prompt content, account linkage, external indicators). They do not need artifact-to-session matching to act. | E02–E06, E08 | Moderate–high |
| I02 | The reverse direction (artifact found in the wild → which session produced it) is a real but **secondary** gap. Public reports describe no case where its absence blocked action. | E02 ("cannot verify off-platform"), absence of counter-evidence | Low–moderate |
| I03 | Providers have the in-house competence and data access to build generation-time fingerprinting (Copilot code referencing proves the pattern). Build-vs-buy strongly favors build. | E10 | Moderate–high |
| I04 | The most dangerous AI-assisted malware authors are exactly the ones who request string encryption and obfuscation, which removes the features binary→source retrieval depends on. | E05, E30 | High (measured on synthetic data) |
| I05 | Binary→source retrieval for **unobfuscated, compiled first-party code** is technically tractable with classical features. The method is not novel (BAT 2011), so differentiation must come from workflow, evidence quality, and access, not algorithms. | E29, E30, E11 | Moderate |
| I06 | Malicious-package detection is a large, paying, crowded market where a new entrant without a data moat is at a disadvantage. | E17, E18, E19 | High |
| I07 | Detection of proprietary code compiled into third-party **binaries/firmware** (as opposed to public source repos) appears under-served by scalable products. It is served today by expert-witness services and desktop forensic suites. | E21, E22, E26, E15 (OSS-only KB) | Low–moderate (absence of evidence is not evidence; needs collection). **Cycle 3:** weakened. Binary→source products exist for OSS (E33, E36, E37). The unserved part is narrowed to *proprietary-code infringement evidence workflows*. |
| I08 | After suppressing known-OSS features, a single owner's proprietary code may overlap with other indexed code less than OSS libraries overlap with each other. If so, binary→source precision would be higher for F than for OSS SCA. It may instead be lower if the proprietary code embeds OSS. | E35 (overlap root cause), E37 (domain-specific harder) | **Untested hypothesis**; gating for revised X1 |
| I09 | Evidence-grade output requires a verification stage after retrieval. Similarity scores alone are insufficient on real binaries. | E35, E36, E50a (filtration) | Moderate–high |

## Cycle 4 entries: frontier-lab malware attribution (doc 15 §3 has full citations)

| ID | Evidence (short) | Source | Grade | Type |
|---|---|---|---|---|
| E51 | GTIG: just-in-time AI malware (PROMPTFLUX, PROMPTSTEAL/LAMEHUG, QUIETVAULT, FRUITSHELL) | [GTIG](https://cloud.google.com/blog/topics/threat-intelligence/threat-actor-usage-of-ai-tools) | B | F |
| E52 | LAMEHUG: APT28 (moderate confidence); about 270 HF tokens (Cato) | [CERT-UA](https://cert.gov.ua/article/6284730); [Cato](https://www.catonetworks.com/blog/cato-ctrl-threat-research-analyzing-lamehug/) | B/C | F |
| E53 | PromptLock PoC using a local Ollama gpt-oss:20b | [ESET](https://www.eset.com/us/about/newsroom/research/eset-discovers-promptlock-the-first-ai-powered-ransomware/) | B | F |
| E54 | Key-format hunting; about 8,000 key-bearing samples in a one-year VirusTotal retrohunt (spoken figure) | [SentinelOne](https://www.sentinelone.com/labs/prompts-as-code-embedded-keys-the-hunt-for-llm-enabled-malware/) | B/C | F |
| E55 | Anthropic: malware on VirusTotal "within 2 hours of Claude generating the code"; indicators shared with partners | [Anthropic PDF](https://www-cdn.anthropic.com/b2a76c6f6992465c09a6f2fce282f6c0cea8c200.pdf) | B | F |
| E56 | GTG-1002 AI-orchestrated espionage; criticized for lacking verifiable indicators | [Anthropic](https://www.anthropic.com/news/disrupting-AI-espionage); [BBC](https://www.bbc.com/news/articles/cx2lzmygr84o) | B/C | F |
| E57 | OpenAI: no evidence the Trellix binaries were generated with its models; cannot verify off-platform activity | [OpenAI PDF](https://cdn.openai.com/threat-intelligence-reports/7d662b68-952f-4dfd-a2f2-fe55b041cc4a/disrupting-malicious-uses-of-ai-october-2025.pdf) | B | F |
| E58 | Anthropic cyber-harms enforcement lead manages analysts "and contractors" | [Greenhouse](https://job-boards.greenhouse.io/anthropic/jobs/5403775008) | B | F |
| E59 | OpenAI external testing includes SME probing; works with expert red-teaming organizations | [OpenAI](https://openai.com/index/strengthening-safety-with-external-testing/) | B | F |
| E60 | Irregular: $80M raise; labs as customers; "several million" first-year revenue (self-reported) | [TechCrunch](https://techcrunch.com/2025/09/17/irregular-raises-80-million-to-secure-frontier-ai-models/); [Forbes](https://www.forbes.com/sites/thomasbrewster/2025/09/16/openai-pays-a-450-million-startup-to-test-chatgpt-capacity-for-evil/) | C | F |
| E61 | Mercor: about $500M gross annualized revenue, mostly from a few labs; experts paid over $85/h on average | [TechCrunch](https://techcrunch.com/2025/10/27/mercor-quintuples-valuation-to-10b-with-350m-series-c/) | C | F |
| E62 | FMF information-sharing agreement covers cyber-threat indicators among 6 member labs | [FMF](https://www.frontiermodelforum.org/updates/fmf-announces-first-of-its-kind-information-sharing-agreement/) | A/B | F |
| E63 | GitHub partner secret scanning covers public repos and npm, not malware repositories | [GitHub docs](https://docs.github.com/en/code-security/concepts/secret-security/secret-scanning-for-partners) | B | F |
| E64 | Malla: backend-LLM attribution of malicious LLM services, P/R 0.87 | [arXiv 2401.03315](https://arxiv.org/abs/2401.03315) | A | F |
| E65 | LLM code model attribution 88–97% closed-world, source-level (preprints) | [2506.17323](https://arxiv.org/abs/2506.17323); [2510.10493](https://arxiv.org/abs/2510.10493); [2506.20197](https://arxiv.org/abs/2506.20197) | B | F |
| E66 | **Measured:** `llm_indicators` credential recall 1.0 on plain, UTF-16, Python and VBScript; 0.0 on split, XOR and base64; 0/5,000 benign system files flagged | `bench/results/llm_indicators/` | Measured | F |
| E67 | **Measured:** benign LLM SDKs (12,174 files): T1 1, T2 69, T3 672; 11/11 packages fire T3+ | same | Measured | F |

| ID | Inference | Basis | Confidence |
|---|---|---|---|
| I10 | Labs already link artifacts and generations in-house. The gap is capacity, RE depth, and off-platform verification, not a tool. | E55, E57, E56 | Moderate–high |
| I11 | A buying channel for outside cyber SME work exists. WTP for malware attribution and enforcement support specifically is unobserved. | E58–E61 | Moderate / unknown |
| I12 | An embedded credential is a provider-verifiable link from sample to account; the holder may be a victim. | E54, E63, E66 | Moderate |
| I13 | Endpoint, model and prompt strings do not indicate malice. | E67 | High (measured) |
| I14 | Small buyer set (about 4–8 realistic labs plus inference platforms); services scale. | E62, E61 | Moderate |

## Cycle 5 entries: RE environments and adjacent pivots (doc 16 §3 has full detail)

| ID | Evidence (short) | Source | Grade | Type |
|---|---|---|---|---|
| E68 | Labs demand RL environments; Anthropic reportedly discussed > $1B over a year | [TechCrunch](https://techcrunch.com/2025/09/21/silicon-valley-bets-big-on-environments-to-train-ai-agents/) | C | F |
| E69 | Contracts often six to seven figures per quarter; $200–$2,000 per task; in-housing rising | [Epoch AI](https://epoch.ai/gradient-updates/state-of-rl-envs) | C | F |
| E70 | Cyber RL-environment vendors (Bugcrowd, Symbiotic, TarantuLabs, Starker) sell to labs; focus on source/web vulnerabilities | [Bugcrowd](https://www.bugcrowd.com/press-release/bugcrowd-launches-reinforcement-learning-environments-to-help-ai-models-learn-real-world-security-skills/) et al. | B | F |
| E71 | Alice Labs benchmark includes a malware-analysis gym with decoys | [Alice](https://alice.io/blog/cyber-rl-benchmark-v1-0-measuring-frontier-cybersecurity-capability) | C | F |
| E72 | SRE-Bench: 5,000 expert hours; public settings fully solve 27–32%; unconstrained 99.2% pass@4 | [arXiv 2608.11469](https://arxiv.org/abs/2608.11469) | B | F |
| E73 | MalwareBench: 12 obfuscated cases; held-out-variant extractor checks; humans > 90% at a median of 12 h | [MalwareBench](https://malwarebench.com/blog/introducing-malwarebench) | B/C | F |
| E74 | CyberSOCEval: malware-analysis accuracy 23–34%; models not trained for cyber analysis | [arXiv 2509.20166](https://arxiv.org/abs/2509.20166) | B | F |
| E75 | OpenAI Daybreak lists malware analysis and RE as authorized workflows; cyber models | [OpenAI Help](https://help.openai.com/en/articles/20001258-openai-daybreak-trusted-access-for-cyber-overview) | B | F |
| E76 | Aardvark → Codex Security | [OpenAI](https://openai.com/index/introducing-aardvark/) | B | F |
| E77 | Snyk–Invariant, PANW–Protect AI, SentinelOne–Prompt Security acquisitions | [Snyk](https://snyk.io/news/snyk-acquires-invariant-labs-to-accelerate-agentic-ai-security-innovation/) et al. | B | F |
| E78 | **Measured:** `re_tasks` on 360 unique instances. L0: strings 19% (decoy trap 67%). L1: XOR brute force 78%. L2: only the family extractor solves (100%). | `bench/results/re_tasks/` | Measured | F |

| ID | Inference | Basis | Confidence |
|---|---|---|---|
| I15 | The largest outside lab spend is on data and environments; cyber is active | E68–E70, E75 | Moderate |
| I16 | Binary-first malware-RE training supply looks thin | E70, E72, E73 | Low–moderate |
| I17 | Fast saturation means recurring demand for fresh tasks, with decaying per-task value | E72, E69 | Moderate |
| I18 | Agent/MCP security and model scanning are absorbed by platforms | E77 | Moderate–high |

## Cycle 6 entries: what labs cannot replicate (doc 17 §3 has full detail)

| ID | Evidence | Source | Grade | Type |
|---|---|---|---|---|
| E79 | EU GPAI Code of Practice App. 3.5: independent external evaluators; no training on their test runs without permission; no retaliation | [Code text](https://docref.org/eu/eu-cop-gpai-safety-and-security/2025/en/) | A | F |
| E80 | Measure 3.5 post-deployment monitoring methods include monitoring known malware and public forums and provenance techniques; independent evaluators get access | As E79 | A | F |
| E81 | Measure 9.2 incident reports need "the model involved" and material "setting out the model's involvement" | As E79 | A | F |
| E82 | Signatories include OpenAI, Anthropic, Google, Microsoft, Amazon, Mistral; xAI Safety & Security chapter only; Meta refused | [Commission](https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai); [Reuters](https://www.reuters.com/technology/musks-xai-sign-chapter-safety-security-eus-ai-code-practice-2025-07-31/) | A/B | F |
| E83 | California SB 53: frameworks describe third-party assessment; critical incidents to Cal OES in 15 days (24 h if imminent); public can report | [Bill](https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202520260SB53) | A | F |
| E84 | Unit 42 AI-assisted intrusion: victim-side view; provider link only from the attacker's claim | [Unit 42](https://unit42.paloaltonetworks.com/ai-assisted-cyber-attack-inside-a-unit-42-investigation/) | B | F |
| E85 | LLMjacking and LLM mixers resell stolen access across 30+ providers | [Sysdig](https://www.sysdig.com/blog/llmjacking-from-emerging-threat-to-black-market-reality); [Pillar](https://www.pillar.security/blog/operation-bizarre-bazaar-first-attributed-llmjacking-campaign-with-commercial-marketplace-monetization); [GTIG](https://cloud.google.com/blog/topics/threat-intelligence/llmjacking-monetizing-compromised-cloud-models) | B | F |
| E86 | Underground AI-abuse markets covered by KELA and Flashpoint | [KELA](https://www.kelacyber.com/press/kela-cyber-finds-200-surge-in-cybercriminals-seeking-ai-to-launch-attacks/); [Flashpoint](https://flashpoint.io/blog/ai-threat-report-monthly/) | B/C | F |
| E87 | Irregular's lab evaluations are pre-deployment and offensive; cited in system cards | [Irregular](https://www.irregular.com/research/evaluating-gpt-5) | B | F |
| E88 | GDPR Recital 26: pseudonymised data remains personal data | [GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj) | A | F |
| E89 | **Measured:** `incident_packet` on 200 synthetic incidents. 0 neutrality violations; routing recall 1.0; 0 leaks of credentials, IPs, emails, hosts, accounts, paths. Leaks: unlisted person names 400/400, external cloud hosts 200/200. First run leaked IPv6 200/200 (fixed). | `bench/results/incident_packet/` | Measured (synthetic) | F |

| ID | Inference | Basis | Confidence |
|---|---|---|---|
| I19 | Labs can replicate whatever money, hiring or acquisition buys; not independence, victim-side presence, cross-competitor neutrality or avoided activities | E55, E57, E69, E72, E79, E83–E86 | Moderate–high |
| I20 | Regulation creates a slot for third-party post-deployment evidence | E80, E81, E83 | Moderate–high |
| I21 | LLMjacking makes single-provider visibility structurally partial | E85, E84 | Moderate |
| I22 | Google is the exception (lab + Mandiant + VirusTotal); other labs' preference for a neutral supplier is untested | E82, E85 | Low–moderate |
| I23 | No vendor found offering post-deployment cyber-misuse evidence shaped for Measure 9.2 (absence of evidence) | E87, E60 | Low |

## Cycle 7 entries: a moat the founder can deliver (doc 18 §3 has full detail)

| ID | Evidence | Source | Grade | Type |
|---|---|---|---|---|
| E90 | AI Office (21 Oct 2026): evaluators need domain expertise and must be "free from the provider's managerial, financial or operational influence" | [Commission](https://digital-strategy.ec.europa.eu/pl/library/requirements-qualified-independent-external-evaluators-general-purpose-ai-models) | A/B | F |
| E91 | AI Office public call and Network of Evaluators; selection on evaluation track record (red teaming, uplift studies) | [Commission call](https://digital-strategy.ec.europa.eu/en/events/call-participants-workshop-qualification-requirements-external-evaluators-gpai-models-systemic-risk) | A | F |
| E92 | Anthropic cyber-jailbreak programme: uplift "beyond … publicly available tools", e.g. "working malware"; internal grading rubric | [HackerOne](https://hackerone.com/anthropic-cyber-jailbreak/) | B | F |
| E93 | Gray Swan: lab- and AISI-sponsored arenas; Shade cyber scoring on "usable operational details"; paid red-team network | [Reflection AI](https://reflection.ai/blog/advancing-open-model-safety-gray-swan) | B/C | F |
| E94 | Critique: evaluator access is voluntary, revocable and often thin | [The AI Realist](https://www.airealist.ai/p/independent-or-current) | C/D | F (claim made) |
| E95 | **Measured:** evaluator controls on 180 instances; canary 180/180 stamped, 0/540 outputs; partitions disjoint; lab-c L1 100% vs 90% p = 0.15 (no claim); 17/17 → CI 0.82–1.00 | `bench/results/re_eval_report/results.json` | Measured (synthetic) | F |
| E96 | **Founder feedback:** DDW-style monitoring and the incident bridge are not realistic for this founder | User, Cycle 7 | Primary | F |

| ID | Inference | Basis | Confidence |
|---|---|---|---|
| I24 | Of doc 17's lab-proof moats, only independence needs no network | E96, E86, A47 | Moderate–high |
| I25 | The financial-influence test also binds the evaluator: no single-lab dependence, no training-data sales to evaluated labs | E90 | Moderate |
| I26 | Judging *working* malware beyond public tools is RE work; public safeguard tests mostly score text | E92, E93 | Low–moderate |
| I27 | Per-customer private banks need expert task families with generated instances for usable CIs | E95 | Moderate |

## Cycle 7 addendum: competitor check (doc 18 §15)

| ID | Evidence | Source | Grade | Type |
|---|---|---|---|---|
| E97 | General Analysis MalwareBench: private malware-RE evaluation on real, zero-detection malware variants; best model 7.6% | [MalwareBench](https://generalanalysis.com/malwarebench) | B | F |
| E98 | Irregular's evaluation taxonomy includes malware development and EDR evasion; deployed with multiple frontier labs | [Irregular](https://www.irregular.com/research/ai-evaluation-platform-cyber-use-case) | B | F |
| E99 | Dreadnode DreadIndex (includes reversing), Booz Allen Cyber Weapon Index, UK AISI/CAISI pre-deployment cyber evaluations | [DreadIndex](https://dreadnode.io/research/introducing-dreadindex-offensive-security-benchmark-for-language-models/); [CWI](https://www.boozallen.com/insights/cyber/cyber-weapon-index.html) | B | F |
| E100 | Uplift adjudication is standardised (Anthropic CJS scale; FMF Jailbreak Rating Framework) and HackerOne independently assesses Anthropic's cyber-jailbreak submissions | [Anthropic](https://www.anthropic.com/news/fable-safeguards-jailbreak-framework); [FMF](https://www.frontiermodelforum.org/specifications/jailbreak-rating-framework-for-frontier-cyber-threats/) | A/B | F |

I23 and I26 are **refuted** by E97–E100.
