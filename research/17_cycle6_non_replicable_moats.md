# 17 — Cycle 6: pivot toward what a frontier lab cannot replicate

**Tasking (user, Cycle 6):** "Keep pivoting. It needs to be something the frontier AI company has trouble replicating."

**How this tasking is handled:**
- "Hard to replicate" becomes an explicit criterion with a stated test (section 4). Anything a lab can get by hiring, spending, or acquiring scores low.
- Personas are **simulated analytical perspectives, not interviewed experts**. No vote was raised to meet a gate.
- No interviews were conducted. Measurements use synthetic data generated in this repository. No real victim data, malware, or credentials were used.

Labels: F = fact (sourced), I = inference, H = hypothesis. Grades A–D as in doc 02.

## Bottom line

1. **Everything sold to labs in Cycles 1–5 is replicable by a lab.** Provenance tooling (A–E), detection feeds (H), SME capacity (M), and RE environments (N/Q) can all be hired or built: labs already do provenance in-house (E55, E57), are in-housing environments (E69), and co-author RE benchmarks (E72).
2. **Four things a lab structurally cannot do for itself** (I19):
   - **Be independent of itself.** The EU Code requires independent external evaluators (E79); SB 53 requires disclosing third-party assessment (E83).
   - **Stand on the victim's side.** Responders see the victim network, and the lab does not (E84, E57).
   - **Be neutral across competitors.** Stolen keys are pooled and resold across 30+ providers via "LLM mixers"; one lab sees a paying customer, not the abuse chain (E85).
   - **Operate where labs won't.** That means victim incident evidence and criminal-market monitoring (E86).
3. **The regulatory slot exists.**
   - EU Code Measure 3.5 lists "monitoring … known malware, public forums" and "provenance techniques" as post-deployment monitoring methods, and gives independent external evaluators access for that monitoring (E80).
   - Measure 9.2 requires serious-incident reports to describe "material … setting out the model's involvement" (E81).
   - OpenAI, Anthropic, Google, Microsoft, Amazon and Mistral signed the full Code; xAI signed the Safety and Security chapter (E82).
4. **Pivot: W, independent cyber-misuse assurance for frontier labs.**
   - V (after deployment): monitor malware, stolen keys and LLM mixers from outside any one lab, and turn victim-consented incident evidence into provider-neutral packets shaped like a Measure 9.2 incident report.
   - R (before deployment): independent malware-RE evaluations from a private task bank. The Code bars labs from training on evaluator test runs without permission.
5. **Measured (X12):** a working slice (`provenance/incident_packet.py`). On 200 synthetic incidents it had **0 cross-provider leaks**, **100% routing** of indicators to the right provider, and **0 leaks** of credentials, IPv4/IPv6, emails, internal hosts, accounts and user paths. Two leaks remain and are not solved: **unlisted personal names (400/400)** and **external cloud hostnames (200/200)**. The first run also leaked IPv6 200/200; that is fixed (0/200).
6. **Scores:** W scores **3.85** under the original weights and **4.00** under the re-weighted matrix, which adds a 15% "lab replication difficulty" criterion. That is the highest in six cycles. N/Q drops from 3.70 to 3.45 under the new weights.
7. **Persona Round 6:** W reaches **9/12** at ≥ 4 after iterations, up from 7/12 in Cycle 5. **No consensus** (gate ≥ 10/12). The remaining holdouts are Privacy Counsel, Supply-Chain Researcher and Skeptical VC, and each needs real-world evidence (section 10).
8. **Decision: PIVOT to W at PILOT FIRST.** BUILD is withheld because the consensus gate fails, no buyer is named, and counsel's review is open.
9. **Honest caveat:** W is hard for **labs** to replicate, but **not** for incumbents.
   - Google is both a lab and the owner of Mandiant, VirusTotal and GTIG. Unit 42, CrowdStrike, KELA and Flashpoint each hold part of W.
   - The moat against them is neutrality and lab focus, which is a hypothesis (H22).

## 1. Intelligence cycle (Cycle 6)

| Stage | What was done |
|---|---|
| Direction | New criterion: a lab must have trouble replicating the offer. PIR-20–22. |
| Collection | EU GPAI Code of Practice (Safety & Security chapter) text and signatories; California SB 53; Unit 42 AI-assisted intrusion case; LLMjacking and LLM-mixer reporting (Sysdig, Pillar, GTIG); underground AI-market reporting (KELA, Flashpoint); incumbent evaluator (Irregular); GDPR Recital 26. One local build and measurement (X12). |
| Processing | E79–E89; inferences I19–I23 |
| Analysis | Replicability test across all candidates A–W; ACH H18–H22; KAC A45–A52; premortem P34–P39; red team; persona Round 6; iterations 19–23; matrix under two weightings |
| Dissemination | This document, plus updates to docs 01, 02, 05, 07, 11, 13, EXECUTIVE_DECISION and README |
| Feedback | X13–X16 with pass/kill thresholds |

## 2. New PIRs

| PIR | Question | Answer | Confidence |
|---|---|---|---|
| PIR-20 | What can a frontier lab **not** get by hiring, spending or acquiring? | Independence from itself, victim-side presence, neutrality across competitors, and activities it avoids for legal or reputational reasons (I19). Acquiring the provider destroys the first and third. | Moderate |
| PIR-21 | Is there a mandated or structural slot for an outside party in labs' cyber-risk process? | Yes. EU Code Appendix 3.5 (independent external evaluators, including for post-deployment monitoring), Measure 3.5 monitoring methods, Measure 9.2 incident fields, and SB 53 third-party disclosure and public incident reporting (E79–E83). | Moderate–high (text is primary; how labs implement it is unknown) |
| PIR-22 | Who else can replicate the offer, and does that kill it? | Google (lab + Mandiant + VirusTotal + GTIG), large IR firms (Unit 42, E84), and underground-intel vendors (E86) each cover part. None was found offering provider-neutral, Measure 9.2-shaped evidence to labs, but that is an absence of evidence. | Low–moderate |

## 3. Evidence (E79–E89)

| ID | Evidence | Source | Grade | Type |
|---|---|---|---|---|
| E79 | EU GPAI Code of Practice, Safety & Security chapter, Appendix 3.5. Signatories "will ensure that adequately qualified independent external evaluators conduct model evaluations" (domain expertise, infosec, confidentiality). Evaluators get access to the most capable versions, chains of thought, and helpful-only versions. Signatories "refrain from training their models on the inputs and/or outputs from such test runs without express permission". No retaliation against evaluators. Exception if no qualified evaluator is found after a public call open 20 business days. | [Code text](https://docref.org/eu/eu-cop-gpai-safety-and-security/2025/en/); [Commission](https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai) | A (official text) | F |
| E80 | Measure 3.5 post-deployment monitoring methods include "monitoring software repositories, known malware, public forums, and/or social media for patterns of use", "privacy-preserving logging and metadata analysis … watermarks, metadata, and/or other … provenance techniques", and "collecting relevant information about breaches of the model's use restrictions". "To facilitate post-market monitoring, Signatories will provide an adequate number of independent external evaluators with adequate free access". Signatories publish selection criteria. | As E79 | A | F |
| E81 | Measure 9.2 serious-incident reports include: dates; harm and affected group; "the chain of events"; "the model involved"; "a description of material available setting out the model's involvement"; and a root-cause analysis of model inputs and outputs. Measure 9.1: review police and media reports and incident databases; facilitate third-party reporting. | As E79 | A | F |
| E82 | Full signatories include Amazon, Anthropic, Google, IBM, Microsoft, Mistral AI and OpenAI (22 in total). xAI signed only the Safety and Security chapter. Meta refused but must comply with the AI Act by other means. | [Commission](https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai); [Reuters](https://www.reuters.com/technology/musks-xai-sign-chapter-safety-security-eus-ai-code-practice-2025-07-31/) | A/B | F |
| E83 | California SB 53 (TFAIA, signed Sept 29, 2025). A large frontier developer's framework must describe "using third parties to assess the potential for catastrophic risks and the effectiveness of mitigations". Critical safety incidents go to Cal OES within 15 days (24 hours if imminent risk of death or injury). The public can report incidents. Anonymized annual reports start in 2027. | [Bill text](https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202520260SB53); [Governor](https://www.gov.ca.gov/2025/09/29/governor-newsom-signs-sb-53-advancing-californias-world-leading-artificial-intelligence-industry/) | A | F |
| E84 | Unit 42 AI-assisted intrusion case: 50+ ATT&CK techniques in under 10 hours; the victim's own AI endpoints were hijacked. "The threat actor told us in negotiations that they leveraged frontier AI models." The responder has the victim's side; the provider link comes only from the attacker's claim. Unit 42 handled 750+ major incidents in 2025. | [Unit 42](https://unit42.paloaltonetworks.com/ai-assisted-cyber-attack-inside-a-unit-42-investigation/); [IR report](https://www.paloaltonetworks.com/resources/research/unit-42-incident-response-report) | B | F |
| E85 | LLMjacking. Stolen cloud credentials are checked against 10 AI services; reverse proxies resell access; victim costs can exceed $46k/day (Sysdig). silver.inc resells access to 30+ providers (Pillar). Google GTIG describes "LLM mixers" and actor UNC6993 using new-api and gcli2api. | [Sysdig 1](https://www.sysdig.com/blog/llmjacking-stolen-cloud-credentials-used-in-new-ai-attack); [Sysdig 2](https://www.sysdig.com/blog/llmjacking-from-emerging-threat-to-black-market-reality); [Pillar](https://www.pillar.security/blog/operation-bizarre-bazaar-first-attributed-llmjacking-campaign-with-commercial-marketplace-monetization); [GTIG](https://cloud.google.com/blog/topics/threat-intelligence/llmjacking-monetizing-compromised-cloud-models) | B | F |
| E86 | Underground AI-abuse markets are already covered by commercial TI vendors. KELA reports a 200% rise in mentions of malicious AI tools and 52% in jailbreak discussions; Flashpoint reports 2.5M+ AI-related illicit posts and tiered API pricing. | [KELA](https://www.kelacyber.com/press/kela-cyber-finds-200-surge-in-cybercriminals-seeking-ai-to-launch-attacks/); [Flashpoint](https://flashpoint.io/blog/ai-threat-report-monthly/) | B/C (vendor) | F |
| E87 | Irregular's evaluations for labs are pre-deployment and offensive (evasion, network exploitation, vulnerability discovery, cyber ranges). They are cited in the Claude 3.7 Sonnet system card and OpenAI's GPT-5 and o3/o4-mini cards. | [Irregular × OpenAI](https://www.irregular.com/research/evaluating-gpt-5); [Irregular × Anthropic](https://www.irregular.com/research/claude-3-7-sonnet-evaluation); [Claude 3.7 card](https://assets.claude.com/9ff93dfa8f445c932415d335c88852ef47f1201e.pdf) | B | F |
| E88 | GDPR Recital 26: pseudonymised data that could be attributed to a person with additional information "should be considered to be information on an identifiable natural person". | [GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj) | A | F |
| E89 | **X12 measured here** (section 5) | `bench/results/incident_packet/` | Measured (synthetic) | F |

| ID | Inference | Basis | Confidence |
|---|---|---|---|
| I19 | A lab can replicate anything bought with money, hiring or acquisition: tools, data, RE talent, evaluation content. It cannot replicate being independent of itself, present on victim networks, neutral among its competitors, or active where it won't go. | E55, E57, E69, E72, E79, E83–E86 | Moderate–high |
| I20 | Regulation creates a slot for third-party post-deployment evidence. Monitoring malware and forums and provenance techniques are named methods, and incident reports must describe the model's involvement. | E80, E81, E83 | Moderate–high |
| I21 | LLMjacking makes single-provider visibility structurally partial. Abuse arrives through victims' legitimate keys, spread across many providers. The lab sees a paying customer, the victim sees a bill, and only an outside view links them. | E85, E84 | Moderate |
| I22 | Google is the exception that proves the rule: it is a lab with Mandiant, VirusTotal and GTIG. Whether other labs prefer a neutral supplier over relying on a competitor's threat intelligence is untested (H22). | E82, E85; Google's ownership of Mandiant and VirusTotal is widely documented (not separately cited) | Low–moderate |
| I23 | Existing external cyber evaluators focus on pre-deployment offensive capability. No vendor was found offering post-deployment cyber-misuse evidence shaped for Measure 9.2. This is an absence of evidence. | E87, E60 | Low |

## 4. Replicability test (all candidates)

Five tests. Each scores 0 (no), ½ (partly) or 1 (yes):
- **T1, independence.** The value requires being outside the lab.
- **T2, off-platform access.** It requires access the lab lacks: victim networks, other providers, criminal spaces.
- **T3, neutrality.** Competitors or victims must trust it, and a lab cannot be neutral.
- **T4, licence.** It does things labs avoid for legal or reputational reasons.
- **T5, compounding.** Its asset (case network, private task bank) accumulates and cannot be bought quickly.

| ID | Candidate (cycle) | T1 | T2 | T3 | T4 | T5 | **Lab replication difficulty (1–5)** | Who else can replicate |
|---|---|---|---|---|---|---|---|---|
| A–E | Provenance tools/architectures (1) | 0 | 0 | 0 | 0 | 0 | **1** (labs do it in-house: E55, E57) | — |
| F | IP code-reuse investigation (2–3) | — | — | — | — | — | n/a (not sold to labs) | SCA vendors |
| H | Embedded-key hunting feed (4) | 0 | ½ | 0 | 0 | ½ | **2** (VirusTotal retrohunt is licensable; Google owns it) | SentinelOne, Google |
| I | Enforcement capacity (4) | 0 | 0 | 0 | 0 | 0 | **1** | Staffing vendors |
| J | Cyber evals / SME probing (4) | ½ | 0 | 0 | 0 | ½ | **2** | Irregular, AISIs |
| M | Safeguards SME services (4) | 0 | ½ | 0 | 0 | 0 | **2** | Contractors |
| N/Q | RE environments (+ M) (5) | 0 | 0 | 0 | 0 | ½ | **2** (E69 in-housing) | Data vendors |
| O/P | Agent supply chain / model scanning (5) | 0 | 0 | 0 | 0 | 0 | **1** | Consolidated platforms (E77) |
| R | Independent malware-RE evaluator (6) | 1 | 0 | ½ | 0 | 1 | **5** (independence is mandated; the bank is protected from training: E79) | Irregular, AISIs (crowded) |
| S | Victim-to-provider incident bridge (6) | ½ | 1 | 1 | ½ | 1 | **5** | Mandiant (Google), Unit 42, CrowdStrike |
| T | Underground AI-abuse HUMINT (6) | 0 | 1 | ½ | 1 | 1 | **5** (labs avoid it in-house; they buy it instead, which is a differentiation problem) | KELA, Flashpoint, Intel 471 (E86) |
| U | AI-involvement forensics for insurers (6) | — | — | — | — | — | n/a (not sold to labs) | IR firms |
| V | Independent post-deployment cyber-misuse monitor: S + public-source T + key/mixer hunting (6) | 1 | 1 | 1 | ½ | 1 | **5** | Google partly |
| **W** | **V + R: independent cyber-misuse assurance, before and after deployment** (6) | 1 | 1 | 1 | ½ | 1 | **5** (the R task bank alone would score lower, but the bundle is sold as independent assurance) | Google partly; no single incumbent found covering both |

Scoring rule, applied mechanically: 1 + (sum of tests), rounded half up. Add 1 more when T1 = 1, because no amount of lab spending satisfies a mandated independence requirement (E79). Cap at 5. Buying the same output from a vendor is **not** lab replication; it is scored under differentiation instead.

**Acquisition risk:** if a lab acquires W, T1 and T3 disappear. That is a fine exit, but not a moat for the acquirer. Positioning must keep multiple labs as customers.

## 5. Measurement this cycle (X12): consent-gated, provider-neutral incident packets

**Code:** `provenance/incident_packet.py`, `tests/test_incident_packet.py` (5 tests), `bench/run_incident_packet_bench.py`.

**What it does.** The broker turns a victim's incident artifacts (binaries and log lines) into one packet per provider, carrying the third-party-suppliable fields of Measure 9.2: period, chain of events, model involved, material on the model's involvement, fields for the provider to complete, and limitations. It enforces:
- A recorded, unexpired victim consent naming the provider. Providers outside the consent are withheld and audited.
- Case-keyed pseudonyms for IPs (v4 and v6), emails, internal hosts, `DOMAIN\user` accounts, user-profile paths, and terms the victim lists.
- Credentials reduced to provider plus last four characters.
- Provider neutrality: other providers' endpoints, keys and model names are masked as `<other-provider>`.
- Investigator role only, and a hash-chained audit entry per packet.
- Every packet states that indicators show configured use of a provider, not that its model wrote the code; that a key may belong to a robbed victim (LLMjacking); and that maliciousness was established by human analysis.

**Benchmark.** 200 synthetic incidents (seed 6). Each plants 10 kinds of victim identifier, including kinds the redactor was **not** designed to catch. One or two providers per incident, with runtime-generated fake keys.

| Identifier kind | First run (`results_before_ipv6_fix.json`) | After IPv6 fix, no name list | After fix, victim lists names |
|---|---|---|---|
| Credential | 0/303 | 0/303 | 0/303 |
| IPv4 | 0/200 | 0/200 | 0/200 |
| **IPv6** | **200/200** | 0/200 | 0/200 |
| Email | 0/200 | 0/200 | 0/200 |
| Internal host | 0/400 | 0/400 | 0/400 |
| Account (`DOMAIN\user`) | 0/200 | 0/200 | 0/200 |
| User-profile path | 0/200 | 0/200 | 0/200 |
| Org name (always listed) | 0/200 | 0/200 | 0/200 |
| **Person name** | 400/400 (no list) | **400/400** | 0/400 |
| **External cloud host** | 200/200 | **200/200** | **200/200** |
| Neutrality violations | 0 | 0 | 0 |
| Routing recall | 1.0 | 1.0 | 1.0 |

**What it shows and does not show:**
- Pattern redaction plus provider masking work on the structured identifiers they target. Neutrality holds by construction.
- **Free-text personal names leak completely** unless the victim supplies a list. **Victim-owned external hosts leak** because they cannot be told apart from attacker infrastructure, which providers need. Both require human review before release (iteration 21).
- Synthetic logs are far cleaner than real ones. These are upper bounds on redaction quality, not field performance.
- Even perfect pseudonymisation leaves **personal data** under GDPR (E88). Redaction reduces risk; it does not remove the need for a lawful basis.

## 6. ACH: which non-replicable offer should be built?

Hypotheses:
- **H18 (= V/W):** independent post-deployment cyber-misuse monitoring + incident evidence (± pre-deployment R).
- **H19:** R alone (pre-deployment independent evaluator).
- **H20:** T alone (underground intelligence).
- **H21:** S alone (incident bridge).
- **H22:** none; labs satisfy these duties with incumbents (AISIs, Irregular, Mandiant/Unit 42, KELA).

| Evidence | H18 | H19 | H20 | H21 | H22 |
|---|---|---|---|---|---|
| E79 independent evaluators required | C | C | N | N | N |
| E80 monitoring malware/forums/provenance named | C | N | C | C | N |
| E81 incident reports need model-involvement material | C | N | N | C | N |
| E83 SB 53 third-party use + public reports | C | C | N | C | N |
| E84 responder has victim side, provider link missing | C | N | N | C | C |
| E85 cross-provider mixers | C | N | C | C | N |
| E86 underground covered by vendors | N | N | **I** | N | C |
| E87 incumbent evaluator, pre-deployment offensive focus | N | **I** | N | N | C |
| E57 OpenAI could only check its own models | C | N | N | C | **I** |
| E89 X12 slice works (with limits) | C | N | N | C | N |
| **Inconsistencies** | **0** | 1 | 1 | **0** | 1 |

Result: H18 and H21 are least inconsistent. H18 includes H21 and adds the evaluator route, which gives access to labs (E79/E80) that a bridge alone lacks. **The most diagnostic missing evidence is any lab saying it would buy post-deployment cyber-misuse evidence from outside** (X15). Without it, H22 cannot be rejected.

## 7. KAC and premortem

| ID | Assumption | Status |
|---|---|---|
| A45 | Labs will accept post-deployment monitoring evidence from a small specialist, not only AISIs or large vendors | **Untested; critical** (X13, X15) |
| A46 | A vendor paid by the lab counts as "independent" under Appendix 3.5 | Unclear: signatories publish their own criteria (E80). Counsel and AI Office guidance needed (X16) |
| A47 | IR firms or victims will share consented, redacted packets | **Untested; critical** (X14). Privilege and liability may block it |
| A48 | Providers want victim-originated packets despite liability and discovery exposure | Untested (X15) |
| A49 | Pseudonymised packets avoid personal-data obligations | **False** (E88). A lawful basis, DPIA and transfer mechanism are needed |
| A50 | Google/Mandiant will not dominate post-deployment evidence for other labs | Hypothesis (H22/I22) |
| A51 | Non-Google labs value neutrality enough to pay | Hypothesis (X15) |
| A52 | Code/SB 53 duties turn into budget, not checkbox self-assessment | Untested |

| ID | Premortem: "W failed because…" | L | S | D | RPN |
|---|---|---|---|---|---|
| P34 | Labs met Appendix 3.5 with AISIs and Irregular and did post-deployment monitoring in-house | 3 | 5 | 3 | 45 |
| P35 | No IR firm would share; the supply side never started | 3 | 5 | 3 | 45 |
| P36 | A packet leaked victim personal data (names or hosts) | 2 | 5 | 4 | 20 |
| P37 | Google offered the same through Mandiant + VirusTotal to all labs | 2 | 4 | 4 | 16 |
| P38 | A lab acquired the company, and independence ended for the other customers | 2 | 3 | 5 | 6 |
| P39 | Monitoring forums drifted into undercover activity, creating legal exposure | 2 | 4 | 4 | 16 |

RPN = L × S × (6 − D). Top risks: P34 and P35 (demand and supply cold start), addressed by X13–X15. P36 is addressed by edge mode plus human review (iteration 21).

## 8. Red team

| Attack | Response |
|---|---|
| "Independence is a compliance checkbox; labs will pick the cheapest evaluator." (VC) | Possible (A52). The private RE bank and post-deployment evidence are the differentiators; price is untested. |
| "Unit 42 already sees 750 incidents a year. Why would it give you anything?" (GTM) | Partner, not compete. The IR firm keeps the client and privilege, and runs the packet builder in edge mode. W supplies the provider-side routing and neutrality the IR firm lacks (E84). Unproven (X14). |
| "Indicators are not attribution." (ML) | Agreed. Packets say so, and the provider completes the root cause from its own logs (Measure 9.2 point 8). W supplies evidence, not verdicts. |
| "Holding victim data plus key fragments makes you a target." (Infra) | Edge mode: raw data stays with the victim or IR firm. W receives only redacted packets. |
| "Forum monitoring is HUMINT by another name." (Privacy) | Public sources only, no personas or purchases. Deeper underground coverage is licensed from incumbents (E86). |
| "A lab can still fund a captive 'independent' shop." (CISO) | True. It would still lack T2 (other victims) and T3 (other labs' trust). |

## 9. Persona Round 6 (simulated)

Votes are on **W after iterations 19–23** (section 11). Columns: importance, technical feasibility, demand, defensibility (now including lab replication difficulty), privacy, founder fit, adoption, overall.

| # | Persona | Imp | Tech | Dem | Def | Priv | Fdr | Adopt | **Ovr** | Justification |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Abuse Investigator | 5 | 4 | 4 | 4 | 3 | 4 | 4 | **4** | Sees behind LLMjacking and victim networks; key suffix plus sample offset is actionable |
| 2 | T&S Eng Lead | 4 | 4 | 4 | 4 | 3 | 4 | 3 | **4** | Maps onto Measure 9.2 fields the lab must fill; volume and quality are unproven |
| 3 | Infra Architect | 3 | 4 | 4 | 4 | 3 | 4 | 4 | **4** | Only with edge mode as default (no raw custody); otherwise 3 |
| 4 | Malware RE | 4 | 4 | 4 | 4 | 3 | 5 | 4 | **4** | Core skill on both sides (evals and incident artifacts) |
| 5 | ML Scientist | 4 | 4 | 4 | 3 | 3 | 4 | 3 | **4** | Eval bank is verifiable (X8); packets deliberately make no model-authorship claims |
| 6 | Supply-Chain Researcher | 3 | 4 | 3 | 4 | 3 | 3 | 3 | **3** | Keys leaked via packages are in scope, but the buyer is not this market |
| 7 | Detection Eng Lead | 4 | 4 | 4 | 4 | 3 | 4 | 4 | **4** | Off-platform indicators feed labs' detections |
| 8 | Forensics Investigator | 5 | 4 | 4 | 4 | 3 | 4 | 4 | **4** | Consent, chain of custody, audit chain and limitations are built in |
| 9 | Privacy Counsel | 3 | 3 | 3 | 4 | **2** | 3 | 3 | **3** | Pseudonymised data is still personal data (E88); names leak without a list (X12); US transfer needs a mechanism |
| 10 | AI Security CISO | 5 | 4 | 4 | 5 | 3 | 4 | 4 | **4** | Regulatory pull plus something labs cannot self-supply |
| 11 | Procurement/GTM | 4 | 4 | 3 | 4 | 3 | 4 | 4 | **4** | Buyer: signatories' frontier-risk/Safeguards owners. Process: Appendix 3.5 evaluator criteria and public calls. No named buyer |
| 12 | Skeptical VC | 4 | 4 | 3 | 4 | 3 | 4 | 3 | **3** | Defensible against labs, not against Google or Unit 42; ~6–10 buyers; services margins; a lab acquisition ends the moat |

**W: 9/12 at ≥ 4, median 4.** Before iterations: V scored 7/12 and W 8/12 (Infra Architect was 3 before edge mode).

| Gate (W) | Result |
|---|---|
| ≥ 10/12 overall ≥ 4 | **Fail (9/12)** |
| No unresolved critical legal blocker | Open, not critical: edge mode + DPIA + transfer mechanism (X16) |
| CISO and Abuse Investigator importance ≥ 4 | **Pass** (5, 5) |
| ML + RE agree validation is valid | Pass for pipelines (X8, X12); synthetic only |
| Procurement identifies buyer and process | Pass on paper; no named buyer |

Other Cycle 6 candidates: R alone 6/12 (crowded: E87); S alone 5/12 (no lab access route); T 2/12 (incumbents: E86); U 1/12 (not a lab product).

**No votes were adjusted.**

### Consensus ceiling: what would move each holdout on W

| Persona (Ovr) | Evidence that would justify ≥ 4 | Obtainable by desk research? |
|---|---|---|
| Privacy Counsel (3) | Written DPIA and lawful-basis opinion for edge mode; transfer mechanism; human-review step for names and hosts | No (X16) |
| Supply-Chain Researcher (3) | A lab or registry buys package-ecosystem key-leak monitoring | No; and a structurally different market |
| Skeptical VC (3) | A paid pilot or LOI from a non-Google signatory, plus evidence it would not default to Mandiant, Unit 42 or Irregular | No (X15) |

**Maximum supportable on desk evidence: 9/12.** Reaching 10/12 needs X15 or X16. Unanimity is not a supportable target (Supply-Chain persona).

## 10. Why this pivot and not another

- The user's criterion removes N/Q as the lead: lab replication difficulty 2 (E69, E72).
- R alone is non-replicable but crowded (E87). S alone is non-replicable but has no access route to labs. T is covered by incumbents (E86).
- W combines the two moats that are structurally out of a lab's reach (independence and off-platform/cross-provider evidence), uses the founder's RE skill, and rides a written regulatory slot (E79–E81, E83).

## 11. Feedback loop (iterations 19–23, candidate W)

W used all five iterations.

| It. | Objection (persona) | Type | Test | Evidence | Result | Change |
|---|---|---|---|---|---|---|
| 19 | "Labs can do it themselves" (VC, CISO) | Business | Replicability test (section 4) | E55, E57, E69, E79, E84, E85 | **Refuted for labs**, except Google (I22) | Target non-Google signatories first; treat Google as partner or later customer |
| 20 | "Incumbents already do it" (GTM, VC) | Competitive | Do Unit 42, KELA or Irregular sell provider-neutral, Measure 9.2-shaped evidence to labs? | E84, E86, E87 | Partly refuted; absence of evidence (I23) | IR firms become the supply partners, not competitors; underground depth is licensed |
| 21 | "Victim data custody and leaks" (Infra, Privacy) | Technical / legal | X12 leak measurement | E89, E88 | Structured identifiers 0 leaks; names and external hosts leak | **Edge mode by default** (builder runs at the IR firm), mandatory victim term list, human review before release |
| 22 | "Indicators are not model involvement" (ML, Forensics) | Analytic | Does the packet overclaim? | X12 packet schema | Accepted | Limitations are built into every packet; the provider completes the root cause |
| 23 | "Is a paid vendor independent?" (Privacy, CISO) | Legal | Appendix 3.5 text | E79, E80 | **Unresolved** (A46) | Counsel and AI Office guidance (X16); keep multiple lab customers |

## 12. Weighted decision matrix under two weightings

Scores (1–5) per criterion. The old weights are as in doc 11. The new weights take 15% for **lab replication difficulty** from need (−5), technical feasibility (−5) and differentiation (−5).

| Criterion | Old wt | New wt | M | N/Q | R | S | T | V | **W** |
|---|---|---|---|---|---|---|---|---|---|
| Unmet need | 20 | 15 | 4 | 4 | 4 | 4 | 3 | 4 | 4 |
| Technical feasibility | 15 | 10 | 4 | 4 | 4 | 3 | 4 | 4 | 4 |
| Differentiation | 15 | 10 | 3 | 3 | 2 | 4 | 2 | 4 | 4 |
| Founder advantage | 10 | 10 | 4 | 5 | 4 | 4 | 3 | 4 | 5 |
| Customer accessibility | 15 | 15 | 3 | 3 | 4 | 2 | 3 | 3 | 3 |
| Willingness to pay | 15 | 15 | 3 | 4 | 3 | UNKNOWN | 3 | 3 | 4 |
| Regulatory/privacy | 10 | 10 | 3 | 3 | 4 | 2 | 2 | 3 | 3 |
| Lab replication difficulty | — | 15 | 2 | 2 | 5 | 5 | 5 | 5 | 5 |
| **Weighted (old)** | | | 3.45 | 3.70 | 3.55 | 3.24 (2.90–3.50) | 2.90 | 3.60 | **3.85** |
| **Weighted (new)** | | | 3.20 | 3.45 | 3.80 | 3.47 (3.10–3.70) | 3.20 | 3.75 | **4.00** |

Notes:
- S's willingness to pay is UNKNOWN. Its weight is excluded and the rest renormalized; the range shows WTP from 1 to 5.
- W's willingness to pay is 4 because the R component sells into evaluation and data budgets that are evidenced (E60, E68–E70). Post-deployment monitoring budget is unevidenced.
- Sensitivity (new weights): W stays ≥ 3.70 if differentiation drops to 3 (an incumbent enters; 3.90), access drops to 2 (3.85), or both drop and WTP falls to 3 (3.60).

History of the best candidate per cycle (old weights): 1.95 → 2.94 → 2.65 → 3.45 → 3.70 → **3.85** (4.00 under the new weights).

## 13. Decision

**PIVOT to W (independent cyber-misuse assurance for frontier labs) at PILOT FIRST.**
- W scores highest under both weightings. Its components R and V also clear the 3.5 line, but each alone has weaker persona support (R 6/12, V 7/12) and a narrower route to buyers.
- BUILD is withheld: 9/12 consensus, no named buyer, A46/A49 open.
- Q (N + M) becomes the fallback, then F at RESEARCH FIRST, then STOP.
- Existing engineering is reused: `llm_indicators` (post-deployment monitoring feed), `incident_packet` (incident evidence), `re_tasks` (R task bank), and service RBAC/audit.

| Experiment | Pass | Kill |
|---|---|---|
| **X13 Evaluator route.** Find signatories' published Appendix 3.5 evaluator criteria and public calls; apply to ≥ 1. | Criteria admit a specialist cyber/RE evaluator, or a call is open | Only AISIs or large firms qualify, and no calls appear within 2 review cycles |
| **X14 Supply side.** 5 IR firms, MSSPs or cyber insurers: would they run edge-mode packet building on consented cases? | ≥ 2 agree to a pilot on a past, consented case | None, because of privilege or liability |
| **X15 Demand side.** 8 conversations with non-Google signatories (Safeguards, frontier risk, compliance), using non-leading questions (doc 15 §14, adapted). | ≥ 2 ask for sample packets **and** ≥ 1 pilot (paid or evaluator agreement) | All say Mandiant, Unit 42, Irregular or in-house covers it |
| **X16 Counsel.** DPIA and lawful basis for edge mode, transfer to US labs, the independence definition (A46), and the SB 53 public-reporting route. | Written opinion with a workable template | Required controls make edge mode infeasible |

Carried over: X5 (public-data hunting pilot) becomes the post-deployment monitoring feed; X9 (hard RE tier) becomes R's private bank.

## 14. Constraint compliance

- No fabricated interviews, votes, sources or results. X12 numbers are from `bench/results/incident_packet/`. The first run's IPv6 leak is kept in `results_before_ipv6_fix.json`.
- Only synthetic incidents; key-shaped strings are generated at runtime. No credential is validated or used, and packets never contain full keys.
- Packets do not claim model authorship; maliciousness is a human determination. Stylistic similarity is not used.
- No real victim data, malware or proprietary code was used or sent to external AI services. The founder's classifier was not present, used, or retrained.
