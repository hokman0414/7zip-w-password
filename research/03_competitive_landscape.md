# 03 — Competitive Landscape

Research date: 2026-11-20. Only products verified via an official or primary source are listed. Pricing is listed only where it is public. "Adoption evidence" lists only what the vendor or a reputable outlet states; customer counts are vendor claims (credibility C) unless noted.

**Direct competition** means a product that answers the same buyer question. **Adjacent** means shared technology or buyer but a different question.

## Summary: what is commoditized vs differentiated

| Proposed capability | Status | Evidence |
|---|---|---|
| Detect "AI-generated code" (stylometry) | **Commoditized, and unreliable in the wild** | E14 |
| Match AI output to *open-source* code (IP/licence) | **Commoditized** (Black Duck, FOSSA/SCANOSS, Copilot, Amazon Q) | E10, E15, E16 |
| Generation-time output fingerprinting inside a provider | **Proven pattern, built in-house** (Copilot code referencing) | E10 |
| Malicious package detection (npm/PyPI/…) | **Crowded, well funded** | E17, E18, E19 |
| Malware code-reuse clustering / genetic attribution | **Established** (Intezer, RL, vendor TI) | E19, E20 |
| Binary→source matching for *open-source* components | **Established** (Black Duck BA, BANG/BAT, BinaryAI) | E11, E15, E29 |
| Coding-agent audit trail / session provenance | **Crowded new category** (Entire, Bitloops, RootBlocks, Hunaru, Backslash) | E27 |
| Proprietary source leak monitoring on *public repos* | **Commoditized** (GitGuardian, Cycode, BigID, Verasity) | E26 |
| Model-output watermarking for code | **Research-stage; not robust** to renaming/obfuscation | E13 |
| **Binary/package → AI-provider generation session** | **No product found**; also no evidence of buyer demand | E02, PIR-5 |
| **Binary/firmware/package → a customer's *proprietary* source, privacy-preserving, evidence-grade** | **No scalable product found.** Served by expert services and desktop forensic suites (CodeSuite/BitMatch). | E21, E22, I07 |

The last two rows are the only candidate whitespace. Row 10 lacks a buyer. Row 11 has a buyer (IP owners, litigators) but needs demand validation.

## Category-by-category

### 1. AI code provenance (session/agent provenance)

| Company / product | Official source | Verified capability | Target customer | Pricing | Deployment | Limitations | Overlap | Adoption evidence |
|---|---|---|---|---|---|---|---|---|
| GitHub Copilot code referencing | [docs](https://github.com/github/docs/blob/main/content/copilot/concepts/completions/code-referencing.md) | Matches suggestions against a public-GitHub index at generation time; block/allow | Copilot users/orgs | Bundled | SaaS, provider-side | Public GitHub only; refreshed every few months; edits not checked | **High for Architecture A**: shows providers build this themselves | Bundled with Copilot |
| Amazon Q code reference log | [docs](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/code-reference.html) | Logs accepted suggestions that resemble public code, with licence | Q Developer users | Bundled | Provider-side | Public-code only | Same as above | — |
| Entire — Checkpoints | [GeekWire](https://www.geekwire.com/2026/former-github-ceo-launches-new-developer-platform-with-huge-60m-seed-round/) | Records reasoning/instructions with AI-generated code | Eng teams using agents | Not public (OSS CLI) | CLI + platform | Records only what runs through it | Medium (session → code link, forward direction) | $60M seed (B) |
| Bitloops | [blog](https://bitloops.com/blog/we-raised-to-build-git-for-ai-coding) | Prompt/decision/model metadata tied to commits | Eng teams | Not public | — | Forward direction only | Medium | EUR 1M round |
| RootBlocks | [site](https://rootblocks.com/) | Signed receipts of agent-built changes; local scanning | Regulated eng orgs | Not public | On-prem engine + cloud | Governance focus | Medium | Not stated |
| Hunaru (Pramana) | [site](https://hunaru.one/) | Hash-chained attribution of agent actions | Eng/compliance | Not public | CLI + hooks | Private pilot | Medium | Private pilot (C) |
| Backslash Security | [Series A note](https://firstraysvc.com/news/backslash-series-a) | Agent/MCP visibility, policy, forensic audit | AppSec | Not public | — | — | Medium (Candidate D) | Named customers: Monday, Chipotle, PandaDoc (C) |

### 2. AI-generated code detection

| Product | Source | Verified capability | Limitations | Overlap |
|---|---|---|---|---|
| Sigrid (Software Improvement Group) | [docs](https://docs.sigrid-says.com/capabilities/faq-ai-code-governance.html) | Stylometric classifier, function level, claims > 95% | Vendor admits noticeable FPs at scale; positioned for trends, not attribution | Low (detection ≠ provenance) |
| Span AI Code Detector | [site](https://www.code-detector.ai/) | span-detect-1, 95% claimed, abstains on about 10% | 6 languages; enterprise sales | Low |
| Copyleaks, GPTZero, Codespy, others | [comparison (secondary)](https://fast.io/resources/best-ai-code-detectors-2026/) | Claimed 90–99% | Mostly self-reported; Span reports a competitor "no better than chance" | Low |
| Independent evidence | [AICD Bench](https://arxiv.org/html/2602.02079), [RealAIGC](https://dlnext.acm.org/doi/10.1145/3832783.3834411) | — | No method generalizes; poor on hybrid code and PRs | **Red flag** for any product based on "this looks AI-written" |

### 3. Binary similarity and attribution

| Product | Source | Capability | Overlap |
|---|---|---|---|
| Intezer | [blog](https://intezer.com/blog/what-is-genetic-malware-analysis) | Code-gene reuse vs a genome DB; links malware families | High for Candidate E (malware clustering) |
| BinaryAI (Tencent, academic + service) | [ICSE'24](https://arxiv.org/abs/2401.11161) | Learned binary→source function matching for SCA | High technically (Architecture B) |
| BinDiff / Diaphora (OSS) | widely known OSS | Binary-to-binary diffing | Medium (needs a reference binary) |

### 4. Software supply-chain provenance and malicious packages

| Company / product | Source | Capability | Target | Pricing | Adoption |
|---|---|---|---|---|---|
| Socket | [Series C](https://socket.dev/blog/series-c) | AI-assisted malicious-package detection, firewall, reachability | Eng/AppSec | Tiers on site (not verified here) | 27k+ orgs; Anthropic, xAI, Cursor named (C); $1B valuation (B) |
| Veracode (Phylum) | [blog](https://www.veracode.com/blog/innovating-secure-software-supply-chains-veracode-acquires-phylum/) | Package firewall, malicious DB | Enterprise | Not public | Acquisition (B) |
| Checkmarx | [product](https://checkmarx.com/product/malicious-packages/) | 550k+ malicious package DB | Enterprise | Not public | (C) |
| JFrog Xray | [docs](https://docs.jfrog.com/security/docs/malicious-package-detection) | Scores every new package; 2–4 h to DB | JFrog customers | Bundled tiers | (C) |
| ReversingLabs Spectra Assure | [docs](https://docs.secure.software/concepts/spectra-assure-analysis) | Whole-package binary analysis; tampering; SBOM | Software producers/buyers | Not public | (C) |
| Datadog GuardDog | [GitHub](https://github.com/datadog/guarddog/) | OSS static + metadata heuristics | Anyone | Free | 1.2k stars |
| SLSA / Sigstore / build attestations | public specs | Build provenance (who built it), not authorship | — | Free | High (ecosystem standard) |

### 5. AI abuse investigation

No commercial third-party product was found that performs provider-side abuse investigation for frontier labs. The capability is in-house (E02–E06), with an inter-lab sharing channel (E08). **Absence of a vendor is not evidence of demand**: it is equally consistent with "providers build this themselves".

### 6. AI agent observability

This category is crowded with general LLM observability (tracing, evals) and the agent-governance players in category 1. It is out of scope beyond noting that it is crowded (E27).

### 7. Malware clustering

Intezer, ReversingLabs, and the large TI vendors (Mandiant/GTIG, CrowdStrike, Microsoft) cluster by code reuse, infrastructure, and TTPs. Founder skills overlap strongly; a new entrant has no corpus advantage (E19, E20).

### 8. Code-generation auditing

This overlaps categories 1 and 2. RootBlocks and Hunaru map to ISO 42001 / SOC 2 evidence (E27).

### 9. Software composition analysis (snippet/IP)

| Product | Source | Capability | Limitation relevant to us |
|---|---|---|---|
| Black Duck Snippet API + Binary Analysis | [blog](https://www.blackduck.com/blog/analyze-ai-generated-code-black-duck-snippet-api.html), [BA](https://www.blackduck.com/software-composition-analysis-tools/binary-analysis.html) | Snippet→OSS project; binary→OSS components | Knowledge base is **open source**. Whether it supports matching against a customer's *private* code at scale was **not verified** (collection gap). |
| FOSSA + SCANOSS | [docs](https://docs.fossa.com/docs/cli/features/snippet-scanning) | Winnowing snippet scan vs OSS index | Source only; OSS only |
| BANG / BAT | [GitHub](https://github.com/armijnhemel/binaryanalysis-ng) | Firmware unpacking, string-based component identification | OSS; expert-driven |

### 10. Model output watermarking

SWEET, STONE, CodeMark, and others (E13) remain research-stage. Robustness to renaming and obfuscation is poor. The approach needs the model provider's cooperation, so it is not an independent vendor play.

### IP investigation: proprietary-code reuse in other products (Cycle 2)

| Product / service | Source | Capability | Gap vs Candidate F |
|---|---|---|---|
| GitGuardian Public Monitoring + source-code leakage | [blog](https://blog.gitguardian.com/pr_code_security_platform_announcement/), [docs](https://docs.gitguardian.com/public-monitoring/sources/overview) | Public GitHub commits/gists; DockerHub layers (limited) | Source repos only; not compiled binaries/firmware/apps |
| Cycode source-code leakage detection | [page](https://cycode.com/source-code-leakage-detection/) | Fingerprints private repos; scans public repos and paste sites | Source only |
| BigID Source Code Protection | [blog](https://bigid.com/blog/bigid-source-code-protection/) | Fingerprinting robust to refactoring; repo scanning | Source only |
| Verasity | [page](https://verasity.ai/use-cases/developer-ecosystem-monitoring) | GitHub/GitLab/npm/PyPI monitoring for leaked code and impersonation | Mostly source/registry metadata |
| SAFE Corp CodeSuite (CodeMatch, **BitMatch**) | [product](https://www.safe-corp.com/products_codematch.htm) | Desktop forensic comparison, source↔source and source↔object code | Expert tool; requires both artifacts in hand; not a monitoring service |
| Expert-witness firms (e.g., Zeidman Consulting) | [site](https://zeidmanconsulting.com/) | Litigation analysis and testimony | Services; post-discovery; expensive per case (price not public) |

**Differentiation hypothesis for Candidate F** (to be validated, not established): a privacy-preserving service in which the IP owner's source never leaves their premises. Only keyed fingerprints are shared, and those are matched against compiled third-party artifacts (binaries, firmware, mobile apps, packages with native code). The service produces reproducible, expert-ready evidence packets and supports pre-filing triage. Existing products cover either *source repos* (E26) or *open-source* KBs (E15, E16), or are *manual expert tools* (E21).

**Counter-hypothesis.** The gap exists because demand is episodic and lawyers prefer bespoke experts. Incumbents (Black Duck, RL, Cycode) could add the feature quickly.
