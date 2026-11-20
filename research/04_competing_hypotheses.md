# 04 — Analysis of Competing Hypotheses (ACH)

## Hypotheses

| ID | Hypothesis |
|---|---|
| H1 | AI providers have a significant unmet need for binary-to-generation-session attribution. |
| H2 | AI providers already possess adequate internal investigation capabilities. |
| H3 | The capability is technically interesting but not commercially important. |
| H4 | Software supply-chain security organizations represent a better initial customer segment. |
| H5 | The most viable product is an internal provider SDK rather than a standalone intelligence platform. |
| H6 | Binary-to-source retrieval is too unreliable after compilation to support the use case. |
| H7 | A narrower source-package provenance and malware-clustering product is more feasible. |
| H8 *(added in Cycle 2)* | The strongest viable business is **IP-owner-side detection of proprietary code compiled into third-party products** (privacy-preserving, evidence-grade). |

## Method

- Each evidence item is scored against each hypothesis: **CC** strongly consistent (+2), **C** consistent (+1), **N** neutral or not applicable (0), **I** inconsistent (−1), **II** strongly inconsistent (−2).
- **Weight** = credibility (A = 1.0, B = 0.8, C = 0.5, D = 0.2) × diagnosticity (1.0 if the item discriminates between hypotheses, 0.5 if partially, 0.2 if it is consistent with almost all).
- ACH ranks hypotheses by **weighted inconsistency** (sum of negative scores × weight). Consistency totals are shown for information only. Absence of evidence is scored N, never C.

## Evidence matrix (Cycle 2, final)

| Evidence | Wt | H1 | H2 | H3 | H4 | H5 | H6 | H7 | H8 |
|---|---|---|---|---|---|---|---|---|---|
| E02 Providers act from the on-platform side; "cannot verify off-platform" | 1.0 | C | C | C | N | C | N | N | N |
| E03/E06 Attribution via indicator overlap and embedded API keys, not code matching | 1.0 | I | CC | C | N | C | N | N | N |
| E04 Recurring reports, automated + human review | 0.5 | C | C | N | N | C | N | N | N |
| E05 Actors request string encryption/anti-debug | 1.0 | I | N | C | N | N | CC | C | I |
| E07 In-memory JIT generated payloads (no artifact) | 0.5 | I | N | C | N | N | C | N | N |
| E08 Inter-lab info sharing exists | 1.0 | I | CC | C | N | C | N | N | N |
| E09 30-day logs; ZDR exclusions | 1.0 | I | N | C | N | C | N | N | N |
| E10 Providers already build generation-time code matching in-house | 1.0 | II | CC | C | N | CC | N | N | N |
| E11 Learned binary→source Recall@1 ≈ 23% at function level | 1.0 | I | N | C | N | N | C | C | I |
| E12 Optimization is the dominant confounder | 0.5 | I | N | N | N | N | C | C | I |
| E17/E18 Supply-chain security is large but crowded | 0.8 | N | N | N | C | N | N | I | N |
| E21 Correlation needs exclusion of alternative explanations | 0.8 | I | N | C | N | N | C | N | C |
| E22 Proprietary code was copied into firmware, with renaming to conceal | 0.8 | N | N | N | N | N | N | N | CC |
| E23 Record trade-secret litigation volume and damages | 0.8 | N | N | I | N | N | N | N | C |
| E26 Source-repo leak monitoring commoditized | 0.5 | N | N | N | N | N | N | N | I |
| E28 AI-written scripts identifiable only through comments/structure | 0.8 | N | N | N | C | N | C | C | N |
| E29 BAT-style string matching is prior art | 1.0 | I | N | C | N | N | N | N | I |
| E30a Measured: hybrid Recall@10 ≥ 0.999 on unobfuscated, stripped, -O3, cross-compiler | 1.0 | C | N | N | N | C | **II** | C | C |
| E30b Measured: escalation recall 0.20 with obfuscated strings + mutated constants | 1.0 | I | N | C | N | N | C | N | I |
| E30c Measured: 0/400 held-out false escalations at calibrated threshold | 1.0 | C | N | N | N | C | I | N | C |
| E30d Measured: IP-transplant (partial module, stripped) Recall@10 1.0; escalation recall 0.88 | 1.0 | N | N | N | N | N | I | N | CC |
| E30e Measured: conventional binary similarity fails cross-optimization (R@10 ≈ 0.03) | 0.5 | N | N | N | N | N | C | N | C |
| E01 Founder classifier/dataset absent | 1.0 | N | N | N | I | N | N | I | N |
| PIR-5 No buyer signal from providers (absence → N, not C) | — | N | N | N | N | N | N | N | N |

## Scores

Inconsistency total = Σ(negative score × weight); lower magnitude is better. Consistency total is shown for context only.

| Hypothesis | Weighted inconsistency | Weighted consistency | ACH reading |
|---|---|---|---|
| H1 Unmet provider need | **−9.6** | +3.5 | **Least likely.** Most diagnostic items contradict it. |
| H2 Providers adequate | 0.0 | +7.5 | Strongly supported, but by provider-published (selection-biased) sources. |
| H3 Interesting, not commercially important (original scope) | −0.8 | +7.6 | **Most likely for the original concept.** |
| H4 Supply chain is a better first segment | −1.0 | +1.6 | Market real; founder wedge unproven. |
| H5 Internal SDK > standalone | 0.0 | +6.0 | Supported. If built, it is a provider-internal feature. |
| H6 Binary→source too unreliable | −3.0 (incl. E30a II) | +4.3 | **Conditionally rejected**: reliable for naive artifacts, unreliable for adversarial ones. The outcome depends on the threat model. |
| H7 Narrower source-package + clustering | −1.8 | +2.9 | Feasible but crowded (E17, E18). |
| H8 IP-owner proprietary-code detection in compiled products | −5.1 | +7.7 | **Most promising new direction**, with real inconsistencies: obfuscation, prior art, and commoditized source-side monitoring. Its demand evidence is indirect. |

Scoring of H6 and H8 needs explanation. H8's inconsistencies (E05, E11, E12, E29, E30b) are all **technical-robustness** concerns. IP infringers are not always adversarial obfuscators: in *Hytera*, the concealment was renaming, which our features survive because strings and constants are rename-invariant (E22). The ACH therefore shifts H8's key uncertainty from "does it work" to "will customers pay".

## Diagnostic insight

The single most diagnostic evidence is **E10 + E08**. Providers already build generation-time matching in-house and already share threat indicators with each other. Together these make H1 implausible as a *vendor* business, whatever the technical results.

The most diagnostic *technical* evidence is the **E30a vs E30b contrast**. Retrieval works when the author is not hiding, and fails when the author is. The commercial question becomes: *which buyer's adversary does not hide?*

- Malware authors working with LLMs explicitly request obfuscation (E05).
- IP infringers frequently do not obfuscate, because shipping products need maintainability and debug strings. They also face different incentives (E22).

## Sensitivity check

- If E10 were wrong (providers do not build such indexes), H1's inconsistency would fall to about −7.6. That is still the worst, so the conclusion is robust.
- If our synthetic corpus overstates distinctiveness (likely; see doc 09 boilerplate-heavy run), H6 gains support for all hypotheses that depend on retrieval (H1, H5, H8). That is the main technical risk to H8.
- If a real buyer commits to a paid pilot for H1, the matrix must be rerun. No such evidence exists today.
