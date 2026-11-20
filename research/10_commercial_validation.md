# 10 — Commercial Validation Plan

**No customer discovery has been conducted.** Everything below is a plan with explicit success and kill criteria. The cells under "What we believe today" are hypotheses grounded in cited evidence, not findings from interviews.

## Segment analysis

| Segment | Who feels the problem | Frequency (hypothesis) | Cost of the problem | Current tools | Why insufficient | Budget owner | Evidence that would justify purchase | What prevents adoption |
|---|---|---|---|---|---|---|---|---|
| AI provider T&S | Abuse investigators | Occasional artifact-first requests (E02) | Investigator hours; reputational exposure | Internal classifiers, account graphs, FMF sharing (E04, E08) | Cannot verify off-platform use (E02) | T&S / Safety | Recurrent cases blocked for lack of artifact→session link | In-house build (E10); data custody (E09) |
| AI provider security eng | Product security | Rare | Low | Internal | — | CISO | — | Not their problem |
| AI infrastructure orgs | Platform teams | Rare | Low | Copilot-style output matching (E10) | — | Eng | — | Build vs buy |
| Supply-chain security vendors | Research teams | Daily (malicious packages) | Core product | Own pipelines (E17, E18) | Provenance rarely changes action | Product/R&D | Provenance improves customer outcomes | They are competitors, not buyers; possible data/OEM partners |
| Enterprise IR teams | IR leads | Per incident | Incident cost | EDR, TI, sandbox | Attribution to AI session is not actionable | CISO | Changed containment decision | No action changes |
| Malware intel vendors | TI analysts | Daily | Core | Intezer/RL-class tooling (E19, E20) | — | R&D | Unique corpus/feature | Have their own |
| **IP owners: embedded/OEM, gaming, security software, semis** *(Cycle 2)* | IP counsel, CTO | Episodic, high stakes (E22) | Lost market share, damages up to hundreds of $M (E22, E23) | Expert witnesses, CodeSuite (E21), source-leak monitors (E26) | Source-only monitors miss compiled products; experts are post-discovery and expensive | **General Counsel / IP** | Credible pre-filing evidence of copying in a competitor's binary | Episodic need; lawful acquisition of artifacts (A16); confidentiality |
| **IP litigation law firms & software-forensics experts** *(Cycle 2)* | Litigators, testifying experts | Per matter; > 1,500 federal trade-secret cases/yr (E23), software share unknown | Expert hours | CodeMatch/BitMatch, manual RE | Manual and slow at binary/firmware scale | Matter budget (client-billed) | Faster, reproducible exhibits | Conservatism; admissibility; firm procurement |
| **M&A technical diligence** *(Cycle 2)* | Diligence providers | Per deal | Deal risk | Black Duck audits (OSS) (E15) | OSS-only; no check for *third-party proprietary* code | Deal team | Found contaminated code pre-close | Price sensitivity; existing vendor relationships |

## 20 customer-discovery questions (non-leading)

These are written to elicit past behavior and actual spend. None of them presupposes that the product is useful.

1. Walk me through the last time you needed to determine where a piece of code came from. What triggered it?
2. What did you do first? Who else got involved?
3. How long did it take from trigger to conclusion?
4. What tools, vendors, or people did you use?
5. What did that cost, including internal time and external fees, roughly?
6. What information did you wish you had and couldn't get?
7. How did you decide the evidence was sufficient to act, or not?
8. What happened as a result of the conclusion?
9. How many times in the last 12 months did a situation like this occur?
10. When it didn't get investigated, why not?
11. Who approved the spend for the last such investigation?
12. What would have to be true for you to spend money on this before a specific incident?
13. What data would you be unwilling to let leave your environment for such an analysis?
14. How do you currently obtain the third-party artifact (binary, firmware, app) you are examining?
15. What has counsel told you about analyzing a competitor's or supplier's binaries?
16. When results were challenged (internally, by opposing counsel, or in court), what was challenged?
17. What would make you distrust an automated similarity result?
18. Which existing tools have you evaluated for this and dropped? Why?
19. If this problem disappeared tomorrow, what would change in your work?
20. Who else in your organization or network deals with this, and could you introduce us?

## Buying signals (measurable; compliments and curiosity do not count)

| Signal | Strength | Threshold for "PILOT FIRST → BUILD" |
|---|---|---|
| Interviewee recounts a specific past case with cost | Weak (problem real) | ≥ 6 of 10 interviews in a segment |
| Willingness to provide test data (own fingerprints, past case artifacts) under NDA | Medium | ≥ 3 organizations |
| Named budget owner and budget source | Medium | ≥ 3 organizations |
| Agreement to an unpaid pilot with defined success criteria | Medium | ≥ 2 |
| **Paid proof-of-concept** | **Strong** | **≥ 2 paid PoCs** |
| Procurement requirements shared (security questionnaire, MSA) | Strong | ≥ 1 |
| Repeat purchase or second matter | Strongest | ≥ 1 within 6 months of the first |

## Discovery plan by candidate

| Candidate | Interviews | Kill criterion |
|---|---|---|
| Original (A/B for AI providers) | 5–8 provider T&S / security leads via founder TI network | < 2 of 8 report ≥ quarterly artifact-first cases, **or** all say "would build" |
| C / E (supply-chain / malware intel) | 8 AppSec leads, 3 vendor research leads | < 3 of 8 describe a decision that provenance would change |
| **F (IP code reuse)** | 12: 4 IP litigators, 3 software-forensics experts, 3 in-house IP counsel (OEM/gaming/security), 2 M&A diligence providers | < 4 of 12 recount a binary/firmware case in the last 24 months, **or** 0 of 12 willing to share test data |

## Pricing hypotheses (untested; do not quote externally)

There are no public prices for comparable binary-IP forensics products. The only anchors are indirect: expert-witness engagements (fees not public) and damages scale (E22, E23). Test two models in discovery:

- per-matter evidence packet
- annual monitoring of a defined competitor or artifact set

Ask for willingness-to-pay *ranges* only after a buyer has described a real past case.
