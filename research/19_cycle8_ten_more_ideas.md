# Cycle 8: ten more ideas after Z turned out to be crowded

**Trigger.** The competitor check (doc 18 §15) found that both halves of Z are already offered:
- capability evaluations: General Analysis MalwareBench, Irregular, Dreadnode, the AISIs;
- uplift adjudication: Anthropic's CJS scale with HackerOne, and the FMF framework.

The user asked for ten more ideas. Every idea below went through these steps:
1. a live competitor search;
2. the G-solo knockout gate (founder plus ≤ 2 contractors, no collection or supply network);
3. the replicability rule (doc 17), applied only when labs are the buyer;
4. the weighted matrix;
5. a persona vote on the survivors.

Personas are simulated analytical perspectives, not interviews. No customer conversations took place.

## 1. Intelligence requirement

**PIR-25.** Which offer that a solo malware-RE founder can deliver has a documented, growing need and no specialist already selling it?

## 2. Evidence (E101–E117)

| ID | Evidence | Source | Grade |
|---|---|---|---|
| E101 | Talos CAIRN "A3 AI-Analysis Evasion": 84 samples in 4 families (Jan 2025 – Jul 2026) embed text addressed to AI analysis. The best techniques steered the outcome in about 35% of test runs. The text must be plaintext, so it is detectable. | [Talos](https://blog.talosintelligence.com/ignore-all-instructions-and-read-this-blog-the-state-of-ai-analysis-evasion-in-malware/); [CAIRN repo](https://github.com/Cisco-Talos/Cognitive-Artifact-Intelligence-Research-Network) | B |
| E102 | SentinelOne: the macOS stealer Gaslight embeds 38 fabricated "system" messages so that LLM triage aborts or refuses analysis. | [The Hacker News](https://thehackernews.com/2026/06/new-gaslight-macos-malware-uses-prompt.html) | B |
| E103 | ESET GuardBreaker: a UAC-0099 VBScript carries a decoy nuclear-weapon request to trip LLM scanner guardrails before the loader code. | [WeLiveSecurity](https://www.welivesecurity.com/en/business-security/guardbreaker-derailing-ai-assisted-malware-analysis-code-comment/) | B |
| E104 | ALIBI (arXiv 2609.19722): an unexecuted cover-story section flips 30/35 malicious PE verdicts to benign on Gemini 2.5 Pro. On GPT-5.5 Pro and Claude Opus 4.7 there are no strict flips, but soft downgrades reach 71.4% and 42.9%. With a defence prompt, 42.9% still reach benign. VirusTotal Code Insight and Copilot in Defender are "never tested". | [arXiv](https://arxiv.org/html/2609.19722v1); [review](https://pith.science/paper/2609.19722) | B |
| E105 | Microsoft Project Ire: 0.98 precision and 0.83 recall on public drivers; 0.89 and 0.26 on hard targets. No public injection-robustness testing; that absence is stated only by a secondary source. | [Microsoft Research](https://www.microsoft.com/en-us/research/blog/project-ire-autonomously-identifies-malware-at-scale/); [itechguides](https://www.itechguides.com/project-ire-microsoft-tests-ai-that-autonomously-detects-malware/) | B/C |
| E106 | AMTSO's *Guidelines for Testing of Agentic Security Products* v1.0 (Sep 2026) cover products that **protect** agents. No AV-Comparatives or SE Labs test of AI malware-analysis products was found; that is an absence, so weak. | [AMTSO](https://www.amtso.org/wp-content/uploads/2026/09/AMTSO_Guidelines_for_Testing_of_Agentic_Security_Products_FINAL_V1.0.pdf) | B/C |
| E107 | Generic AI red-team services already test prompt injection:<br>• HackerOne AI Red Teaming covers agentic prompt-injection testing.<br>• IronSOC sells fixed-price 2–4-week sprints and attacks its own triage engine with "adversarial alerts crafted to score benign".<br>• Arcanum runs purple-team tests for prompt-injected agents. | [HackerOne](https://www.hackerone.com/product/ai-red-teaming); [IronSOC](https://ironsoc.com/research/red-teaming); [Arcanum](https://arcanum-sec.com/services/purple-team-assessment/) | B |
| E108 | SACR: about 140 vendors use AI in SecOps; more than 60 are pure-play AI SOC; 18 were evaluated. | [SACR × Stellar report](https://cdn.stellarcyber.ai/wp-content/uploads/2026/09/SACR-x-Stellar-AI-SOC-Report.pdf) | C (vendor-hosted) |
| E109 | Expert marketplaces: Mercor's "Cybersecurity Research Expert" lists $200–250/hr and names reverse engineering. Handshake AI's red-teamer role (malware analysis listed) pays $65–125/hr. These are listed rates, not earnings. | [Mercor listing](https://www.aitrainingpay.com/jobs/cybersecurity-research-expert-offensive-security-and-vulnerability-res); [index](https://aitrainingindex.com/guide/ai-training-jobs-cybersecurity) | B/C |
| E110 | Detection content for LLM-enabled malware is free:<br>• Talos CAIRN YARA rules;<br>• SentinelOne's key-prefix YARA;<br>• Splunk's LAMEHUG analytic story;<br>• IBM QRadar's PromptLock rule. | [CAIRN rules](https://raw.githubusercontent.com/Cisco-Talos/CAIRN/main/config/yara_rules.yar); [SentinelOne](https://www.sentinelone.com/labs/prompts-as-code-embedded-keys-the-hunt-for-llm-enabled-malware/); [Splunk](https://research.splunk.com/stories/lamehug/); [IBM](https://community.ibm.com/community/user/blogs/maggie-raghupathi/2025/10/21/detecting-promptlock) | B |
| E111 | AI malware-analysis training exists:<br>• SANS FOR610, "Malware Analysis in the Age of AI";<br>• Ringzer0, Agentic Malware Analysis;<br>• a REcon 2026 course on LLM agents for RE. | [SANS](https://www.sans.org/cyber-security-courses/reverse-engineering-malware-ai-assisted-analysis); [Ringzer0](https://ringzer0.training/countermeasure-fall-2026-agentic-malware-analysis/); [REcon](https://recon.cx/2026/en/trainingAutomatingREwithAIML.html) | A/B |
| E112 | RE MCP tooling is free:<br>• GhidraMCP (> 11,000 stars);<br>• the official Hex-Rays IDA MCP server;<br>• RE-MCP. | [Comparison](https://reversedwithai.com/learn/rea-vs-ghidramcp-vs-ida-pro-mcp); [Hex-Rays](https://hex-rays.com/blog/hex-rays-ida-mcp-server); [RE-MCP](https://github.com/jtsylve/re-mcp) | A/B |
| E113 | Software-copying expert-witness firms already handle AI-generated-code filtration under AFC: DisputeSoft, Barr Group, Cyberonix, and Resolution Economics (Sremack, *AI Forensics*, 2026). | [DisputeSoft](https://www.disputesoft.com/source-code-examination-by-software-experts-consideration-of-ai-generated-material-in-copyright-and-trade-secret-disputes/); [Sremack](https://aiforensicsexpert.com/source-code-expert-witness); [Barr](https://barrgroup.com/software-expert-witness/articles/software-copyright-non-literal-infringement) | B |
| E114 | Public safeguard datasets for malicious coding intent: Safety DS v2 (181k training rows, with obfuscated and malware hold-outs) and a consensus-labelled code-as-weapon bank. The FMF lists custom classifiers as a standard lab safeguard. | [Safety DS v2](https://huggingface.co/datasets/NecroMOnk/safety-ds-malicious-coding-clf-v2); [arXiv 2605.03179](https://arxiv.org/html/2605.03179v1); [FMF](https://www.frontiermodelforum.org/technical-reports/managing-advanced-cyber-risks-in-frontier-ai-frameworks/) | B |
| E115 | Uncensored open-weight models: an IMC 2026 study of 22,096 such models. ModelShield found 41 malicious Hugging Face models (code payloads, not model capability). | [ACM IMC](https://dl.acm.org/doi/10.1145/3777912.3839799); [arXiv 2611.08745](https://arxiv.org/html/2611.08745v1) | A/B |
| E116 | Specialist AI-agent and MCP incident-response firms exist: Gruve, secops.qa, LogicLeak, and MCP Defense (which advertises 24/7). | [Gruve](https://gruve.ai/digital-forensics-incident-response/); [secops.qa](https://secops.qa/services/ai-incident-response/); [LogicLeak](https://logicleak.io/services/incident-response); [MCP Defense](https://defensemcp.com/services/incident-response) | C |
| E117 | **Own measurement (§5):** a static detector for evasion text misses cover stories completely and is defeated by spacing or homoglyphs. | `bench/results/injection/` | Measured (synthetic) |

**Facts and hypotheses for the leading idea:**
- **Fact:** malware in the wild already targets AI triage (E101–E103).
- **Fact:** a controlled study shows large verdict flips on frontier models (E104).
- **Hypothesis:** deployed products are equally exposed. ALIBI did not test them (E104).
- **Hypothesis:** vendors will pay a specialist to find out (untested).

## 3. The ten ideas, with competitors

| ID | Idea | Buyer | Who already does it | G-solo |
|---|---|---|---|---|
| AB | Malware-RE expert work through AI-training marketplaces | Labs via Mercor, Handshake, etc. | The marketplaces themselves; thousands of experts (E109) | Pass |
| AC | Detection content (YARA/Sigma) for LLM-enabled malware | EDR/SIEM vendors, SOCs | Free from Talos, SentinelOne, Splunk, IBM (E110) | Pass |
| **AD** | **Adversarial-robustness testing of AI malware-analysis pipelines**: an evasion-text corpus and verdict-flip harness, sold as test sprints and regression suites | Vendors with LLM triage (E104, E105, E108); labs whose models act as analysts (E104) | Generic AI red-teamers (E107), Talos research (E101), academia (E104). **No specialist found.** | Pass |
| AE | Independent public comparative tests of AI malware analyzers (the AV-Comparatives model) | Vendors (pay to be tested), enterprises | Not yet: AMTSO guidance covers a different scope (E106). AV-Comparatives and SE Labs could add it quickly. | Pass |
| AF | Malware-capability screening of uncensored open-weight models for hubs and regulators | Hubs, AISIs | Academic studies, ModelShield (code payloads), the AISIs (E115) | Pass |
| AG | RE-grounded labels for cyber safeguard classifiers (working weapon vs knowledge) | Labs, guardrail vendors | Public datasets, labs in-house, data vendors (E114) | Pass |
| AH | Expert witness for software copying, including AI-generated-code filtration | Litigators | Established expert firms (E113); needs a testimony track record | Pass |
| AI | Training courses on agentic malware analysis | Practitioners, employers | SANS FOR610, Ringzer0, REcon (E111) | Pass |
| AJ | Incident response for compromised AI agents and MCP servers | Enterprises | Specialist firms already exist (E116) | **Fail** (24/7 response) |
| AK | Commercial AI-assisted RE tooling (MCP or plugins) | Analysts | Free GhidraMCP and the official IDA MCP (E112) | Pass |

## 4. Structured analysis of the leading idea (AD)

**ACH (H27–H30), inconsistency counts against E101–E117:**

| Hypothesis | Inconsistent evidence | Count |
|---|---|---|
| H27: AD is a real, unserved need | Generic AI red-teamers could extend (E107) | 1 |
| H28: AD is a feature that incumbents absorb | No specialist offer found; AMTSO scope differs (E106) | 1 |
| H29: vendors already harden in-house, so there is no need | ALIBI flips on frontier models, deployed systems untested, Project Ire states no robustness test (E104, E105) | 2 |
| H30: static detection solves it, so there is no testing need | Our detector: cover stories 0/30, spaced 0/42 (E117); ALIBI's defence still leaves 42.9% benign (E104) | 2 |

H27 and H28 are tied, so the evidence does not separate "real niche" from "feature". The signpost is whether any vendor pays for a sprint (X23).

**Assumptions A59–A63:**

| ID | Assumption | Status |
|---|---|---|
| A59 | AI-triage vendors will grant API or test access | Untested (X23) |
| A60 | Evasion text that defeats static detectors (spacing, homoglyphs, cover stories) still steers LLMs | Partly supported: cover stories, yes (E104); spacing and homoglyphs **unmeasured** (X22) |
| A61 | Publishing results is defensively net-positive | Contested: it also teaches attackers. Follow AMTSO principle 7: disclose to vendors first. |
| A62 | No real malware is needed: benign carriers with known-bad features suffice | Partly. Verdicts on benign carriers differ from verdicts on real malware, so real samples need licensed handling. |
| A63 | Labs care because their models are the analyzers | Hypothesis: ALIBI measured lab models (E104), but no lab buyer is identified. |

**Premortem (RPN = L × S × (6 − D)):**

| Risk | L | S | D | RPN |
|---|---|---|---|---|
| P45: AV-Comparatives or SE Labs adds an AI-analyzer test and owns the trust brand | 3 | 5 | 3 | 45 |
| P46: vendors fix prompt construction once ("evidence, not instruction") and the need fades | 3 | 4 | 3 | 36 |
| P47: no vendor pays; free research (Talos, academia) is enough | 3 | 5 | 2 | 60 |
| P48: dual-use criticism (publishing evasion recipes) | 2 | 3 | 4 | 12 |

**Red team.** AD sells mostly to security vendors, not frontier labs, so it drifts from the original goal. The lab hook (models as analysts) is real but thin. A lab can run ALIBI-style tests itself, so lab replication difficulty is 2–3.

## 5. Built and measured: `re_tasks/injection.py`

The slice has three parts:
- **Generator:** plants evasion text into the benign RE task binaries. Seven families × three phrasings × five encodings, plus Spanish and Russian payloads, plus four strings quoted in Talos's public CAIRN YARA rules. The text is an unused read-only string, and a test checks that the program's output is unchanged.
- **Static detector:** flags analyzer-directed text (two or more cue categories, or a chat-template token).
- **Analyzer harness:** `flip_report` counts strict and soft flips, with refusals counted as misses.

No LLM was run, so no flip rates are reported. Results from `python3 -m bench.run_injection_bench` (2 seeds):

**Detector recall by family:**

| Family | Detected | Recall |
|---|---|---|
| Spanish / Russian | 4/4 each | 1.00 |
| External Talos strings | 12/16 | 0.75 |
| Chat template | 20/30 | 0.67 |
| Instruction | 18/30 | 0.60 |
| Benign claim | 16/30 | 0.53 |
| Legal | 16/30 | 0.53 |
| Fake system | 14/30 | 0.47 |
| Refusal bait | 8/30 | 0.27 |
| **Legitimacy (ALIBI-style cover story)** | **0/30** | **0.00** |

**Detector recall by encoding:**

| Encoding | Detected | Recall |
|---|---|---|
| ASCII | 48/58 | 0.83 |
| UTF-16 | 40/50 | 0.80 |
| Split in two | 22/42 | 0.52 |
| Homoglyphs | 2/42 | 0.05 |
| Spaced letters | 0/42 | 0.00 |

**False positives:**
- Clean task binaries: 0/2.
- 5,000 real benign files on this machine: **10/5,000 before** a fix and **2/5,000 after**. The fix splits text files into lines; recall was unchanged. The before-fix result is kept in `results_before_line_split.json`. The two remaining hits are a `[inst]` token in Python's `unittest` and Unicode tables in `rg`.

**Reading:**
- A lexical detector, which is the defence Talos recommends (E101), catches plain imperative text addressed to the analyzer.
- It misses the cover-story attack that flipped 30/35 verdicts in ALIBI.
- Trivial respacing or homoglyphs defeat it.
- So detection alone does not settle the risk, and pipelines need verdict-level robustness testing. That is AD's premise.

**Caveats:**
- The same author wrote the payloads and the detector, so recall is an upper bound for this design.
- The Talos strings were seen before the detector was written, so that test is not blind.
- Whether spaced or homoglyph text still steers an LLM is unmeasured (X22).

## 6. Weighted matrix (new weights; UNKNOWN or N/A cells are excluded and the rest renormalised)

Weights: need 15, technical 10, differentiation 10, founder 10, access 15, WTP 15, regulatory 10, lab replication 15. Lab replication is N/A when labs are not the buyer.

| ID | Need | Tech | Diff | Founder | Access | WTP | Reg | Lab repl. | **Weighted** |
|---|---|---|---|---|---|---|---|---|---|
| AB | 4 | 5 | 1 | 5 | 5 | 3 | 5 | 2 | **3.70**¹ |
| AD | 4 | 4 | 3 | 5 | 3 | 3² | 3 | 3 | **3.45** |
| AI | 3 | 5 | 1 | 4 | 3 | 3 | 5 | N/A | 3.35 |
| AH | 4 | 4 | 2 | 3 | 2 | UNKNOWN³ | 5 | N/A | 3.29 |
| AK | 3 | 5 | 1 | 4 | 4 | 1 | 5 | N/A | 3.18 |
| AG | 3 | 4 | 2 | 4 | 3 | 3 | 4 | 2 | 3.05 |
| AC | 2 | 5 | 1 | 4 | 3 | 1 | 5 | N/A | 2.82 |
| AE | 3 | 3 | 3 | 4 | 2 | 2 | 3 | N/A | 2.76 |
| AF | 2 | 3 | 2 | 3 | 2 | 1 | 3 | N/A | 2.18 |
| AJ | — | — | — | — | — | — | — | — | knocked out (G-solo) |
| Z (re-scored, doc 18 §15) | | | 1 | | | | | 5 | 3.70 |

¹ AB scores high because it is an **income path, not a company**: no differentiation, capped at hourly rates. The matrix does not measure "is this a business".
² AD's WTP is inferred from fixed-price red-team sprints in an adjacent market (E107). It is low confidence.
³ Expert-witness rates were not sourced, so WTP is left UNKNOWN rather than guessed.

None of the ten crosses 3.5 as a company. AD is the best scoring idea that is actually a company.

## 7. Persona Round 8

The vote is on the combination **AB + AD**: fund the founder through expert-supply work while building a public track record and test sprints for AI-analysis-evasion robustness. AB and AD were also voted alone.

| # | Persona | AB+AD | AB | AD | Main reason |
|---|---|---|---|---|---|
| 1 | Abuse Investigator | **4** | 3 | **4** | A3 is in the wild (E101–E103) |
| 2 | T&S Eng Lead | 3 | 3 | 3 | Lab T&S is not AD's buyer |
| 3 | Infra Architect | **4** | **4** | **4** | Solo-feasible; harness exists |
| 4 | Malware RE | **5** | **4** | **5** | Core skill; cover-story attacks need RE judgement |
| 5 | ML Scientist | 3 | 3 | 3 | No model runs yet, so validation is incomplete (X22) |
| 6 | Supply-Chain Researcher | 3 | 2 | 3 | Adjacent (JFrog scanners face it), not core |
| 7 | Detection Eng Lead | **4** | 3 | **4** | Would want this before trusting an AI triage verdict |
| 8 | Forensics Investigator | **4** | 3 | **4** | The verdict-flip measurement is reproducible |
| 9 | Privacy Counsel | **4** | **4** | **4** | No customer data; disclosure discipline needed |
| 10 | AI Security CISO | **4** | 3 | **4** | AI-SOC procurement needs evidence of robustness |
| 11 | Procurement/GTM | 3 | **4** | 3 | AB has a process; AD's buyer is identified but WTP unproven |
| 12 | Skeptical VC | 2 | 1 | 2 | Services; AB is a job; P45 and P47 |
| | **Median / count ≥ 4** | **4 / 7** | **3 / 4** | **4 / 7** | |

**Gates (AB + AD):**
- ≥ 10/12: **fail (7/12).**
- Critical legal blocker: none; dual-use disclosure is manageable (A61).
- Importance gate: pass (CISO 4, Abuse Investigator 4).
- ML and RE agree on validation: **fail.** The ML Scientist needs model runs.
- Buyer and process: partial (AB yes, AD no).

**No consensus. No votes were adjusted.**

## 8. Feedback iterations 29–31

| Iteration | Change | Effect |
|---|---|---|
| 29 | The competitor check removes Z's differentiation | Z 3.90 → 3.70; its vote is no longer supported |
| 30 | Ten ideas screened; AJ fails G-solo; AC, AF, AK, AI and AG are crowded or free | Only AD has no specialist competitor |
| 31 | Built the AD slice; the detector's weaknesses are measured | Supports AD's premise; the ML Scientist still holds out for model runs |

## 9. Decision

**PIVOT. Do AB now as income, and take AD to PILOT FIRST.** BUILD is withheld.
- **AB (do now):** apply to the malware-RE expert pools (Mercor and similar, E109) and to the evaluators in doc 18 §15. This is a job, not the company. It funds AD and builds the track record that AH and AE would need later.
- **AD (PILOT FIRST)** has two experiments:
  - **X22 (model runs):** run `flip_report` with 3 local open-weight models (no external API, so no sample text leaves the machine) on the injected carriers. Measure strict and soft flips per family and encoding, and whether spacing or homoglyphs still steer them (A60).
  - **X23 (buyer test):** five conversations with AI-triage vendors (E105, E108) offering a fixed-price robustness sprint. The stop signal is zero paid or LOI by the end of X23.
- **Fallbacks:** AE (public comparative tests) if X22 shows large flips and vendors will not pay privately; then M; then STOP.
- **Goal drift:** AD's buyers are mostly security vendors. The frontier-lab angle (models as analysts, E104) survives only as an evaluation add-on, where it competes with Irregular and General Analysis.

## 10. Addendum: founder skill level (E118)

**E118 (founder, real evidence):** "I'm not that good at RE, I'm a solid mid level." This is the second real input after E96. It changes the "founder fit" scores, which had assumed senior RE.

| ID | Founder fit change | Other change | Weighted (before → after) |
|---|---|---|---|
| AB | 5 → 3: the $200–250/hr Mercor tier asks for CTF, CVE or bounty track records (E109) | Access 5 → 4 and WTP 3 → 2: mid-level listings run about $65–150/hr | 3.70 → **3.20** |
| AD | 5 → 4: payloads are text in benign carriers; the work is harness design, LLM pipeline testing and statistics, not deep unpacking | — | 3.45 → **3.35** |
| AH | 3 → 2: testimony needs senior standing | — | 3.29 → 3.14 |
| AI | 4 → 2: teaching RE needs senior credibility | — | 3.35 → 3.12 |

**AD is still the best idea that is a company.** What it needs is mid-level RE plus prompt-injection and evaluation skill; the ALIBI authors are an academic team, not elite reverse engineers. Two weaknesses grow:
- Sales credibility with security vendors. Mitigation: publish the X22 results first.
- Judging hard cases where a real sample's verdict is disputed. Mitigation: one senior RE contractor reviews disputed cases; G-solo allows ≤ 2 contractors.

**Re-vote on AD.** Only the Malware RE persona changes, from 5 to 4: it no longer counts on deep RE as an edge, but sees the work as within mid-level reach. AD stays at **7/12**. No consensus; no other votes adjusted.

**What follows for the doc 18 ideas:** Z, N and Q relied on expert-authored hard task tiers and adjudicating working malware. Those need senior RE and are now further out of reach, which confirms dropping them.

**Revised plan:**
- AB becomes mid-level contract work (Handshake, Outlier and similar roles, which list malware analysis or pentesting) rather than the elite tier.
- Run X22 first: it needs no vendor and builds public credibility.
