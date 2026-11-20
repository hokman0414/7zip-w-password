# 08 — Technical Feasibility

All quantitative claims below come from `bench/results/` (E30), produced by `python3 -m bench.run_benchmark`, or from cited literature. Synthetic-data caveats apply throughout (doc 09 §Threats to validity).

## Architecture A — Provider-side provenance SDK

| Step | Feasibility | Evidence / notes |
|---|---|---|
| 1. Identify generated code artifacts | Feasible; fenced code blocks, tool-call file writes, agent diffs | Streaming must be buffered to artifact boundaries; agent sessions produce multi-file artifacts |
| 2. Extract normalized fingerprints | Feasible; ≈ 116 features/record, ms-scale | E30 cost: index build 10k records in 10.2 s single-threaded Python |
| 3. Associate with provider session refs | Trivial inside provider | Opaque ref only; resolution stays in provider systems |
| 4. Access-controlled index | Implemented in slice | Keyed HMAC, case-gated queries, hash-chained audit |
| 5. Retention/deletion | Implemented in slice | TTL purge and delete propagate to postings (tests) |
| 6. Authorized investigative retrieval | Implemented in slice | `InvestigationService.investigate` |
| **Overhead** | ~1.5 KB/artifact keyed storage; sub-ms search at 10k | E30 |
| **Blocking issues** | ZDR/30-day retention (E09); build-vs-buy (E10); composite multi-session authorship (E02, E04) | — |

**Verdict:** technically easy, commercially weak for a vendor. Best realized *by providers themselves*, or as open-source reference code.

## Architecture B — Binary-to-source retrieval engine

| Step | Status in slice | Measured result / gap |
|---|---|---|
| 1. Format/arch identification | ELF x86-64 only | PE, Mach-O, ARM not implemented |
| 2. Strings and constants | Implemented (with `puts`/`fwrite` aliasing and ±1 compare normalization) | Survive -O0…-O3, gcc/clang, strip (E30a) |
| 3. Compiler/library artifacts | Imports only (low weight) | No compiler fingerprinting yet |
| 4. Function-level representations | Not implemented | Literature R@1 ≈ 0.23 learned (E11) |
| 5. Structural fingerprints | Opcode 5-gram baseline only | Fails cross-optimization: R@10 0.03 at gcc-O2 vs O0 refs (E30e) |
| 6. Search reference corpus | Implemented (inverted index, IDF, df cap) | 0.28 ms median at 10k records |
| 7. Rank candidates | Implemented | Hybrid R@10 ≥ 0.999 default; 0.91 stripped -O3 under boilerplate-heavy |
| 8. Explainable evidence | Implemented | Matched query-side features + per-type counts + limitations |
| 9. Return no-match | Implemented (score, distinct-feature, and margin gates) | 0/400 held-out false escalations (both corpora) |

**Where it breaks (measured):**

| Condition | Hybrid Recall@10 (default → boilerplate-heavy) | Escalation recall at ≤ 1% FER |
|---|---|---|
| gcc -O3 stripped | 1.000 → 0.912 | 0.991 → 0.582 |
| clang -Os stripped | 0.999 → 0.894 | 0.987 → 0.526 |
| constants modified, stripped | 0.999 → 0.858 | 0.974 → 0.408 |
| strings obfuscated, stripped | 0.992 → 0.812 | 0.907 → 0.272 |
| strings obfuscated + constants modified | 0.768 → 0.348 | 0.200 → 0.010 |
| IP transplant (2 donor functions in a new host, renamed, stripped) | 1.000 → 0.660 | 0.880 → 0.135 |

**Verdict:** feasible for naive and unobfuscated targets; not feasible against deliberate obfuscation without new feature classes (decompiled-structure embeddings, dynamic traces), and even those are weak in the literature (E11). The open-set gate holds on synthetic data. The cost of safety is low recall, not wrong answers.

## Architecture C — Supply-chain provenance intelligence

| Step | Feasibility | Notes |
|---|---|---|
| 1–2. Metadata, extract source and bundled binaries | Mature (GuardDog, BANG) | E18, E29 |
| 3. Malware ML model as one signal | **Blocked**: model not present (E01) | Adapter boundary implemented (`provenance/classifier.py`). Reports state "not assessed" |
| 4–5. Code reuse and clustering | Feasible (same index; source-side winnowing helps where structure is diverse) | Winnowing was uninformative on our templated corpus (R@1 0.04): a corpus limitation, not a verdict |
| 6. Compare with authorized provenance records | Same as A/B | — |
| 7. Evidence report | Implemented | — |

**Verdict:** technically the easiest, because source packages retain comments and structure (E28). Commercially the most crowded (E17, E18).

## Architecture F (Cycle 2) — Owner-custodied proprietary-code fingerprinting vs third-party compiled artifacts

This reuses B's engine with the custody inverted:

1. The IP owner runs the extractor on-prem over their source. Only keyed fingerprints and the key ID leave; the key stays on-prem, or matching runs entirely on-prem.
2. Suspect artifacts (competitor firmware, apps, SDKs, package native addons) are unpacked (BANG-class tooling) and feature-extracted.
3. Containment-oriented matching asks "what fraction of my module's distinctive features appear in this artifact". This is implemented as `Candidate.containment`.
4. Output is an expert-ready evidence packet: artifact hashes, extractor version, matched features with locations, alternative-explanation checklist (E21), and a reproducibility script.

Measured relevance: the IP-transplant condition directly models "two proprietary functions renamed and embedded in another product, stripped". Recall@10 is 1.0 on the default corpus and 0.66 on the boilerplate-heavy corpus, with zero wrong escalations in both.

## Comparison

| Criterion | A Provider SDK | B Binary→source engine | C Supply-chain intel | F IP code-reuse |
|---|---|---|---|---|
| Technical feasibility | High | Medium (naive) / Low (adversarial) | High | Medium–High (non-adversarial infringers) |
| Commercial demand | Low (E10, PIR-5) | Low as standalone | High but crowded | Unknown; plausible (E22, E23) |
| Privacy | Good if provider-hosted | Depends on corpus custody | Good (public data) | Good (owner-held key); A16 open |
| Cost | Low | Medium (format coverage) | Medium (data scale) | Medium (unpacking, evidence QA) |
| Integration complexity | High (inside provider stacks) | Medium | Medium | Low–Medium (on-prem CLI + service) |
| Founder advantage | Low | Medium–High (RE) | Low–Medium (assets unverified) | **High (RE + forensics)** |

## Phase 6 — Existing asset validation (protocols; assets were not available)

**Status: neither asset exists in this repository (E01). Nothing below has been executed.** These are the acceptance protocols the founder's assets must pass before any roadmap item depends on them.

### A. Malware ML classifier

| Check | Protocol | Pass criterion (provisional) |
|---|---|---|
| Independent ground truth | Labels from ≥ 2 independent sources (sandbox behavior + analyst confirmation), not AV consensus alone | Documented label provenance for 100% of the test set |
| False-positive rate | Large benign corpus (signed vendor software, OS binaries, popular OSS builds, clean installers) | FPR ≤ 0.1% at the operating threshold (tune per use) |
| Precision/recall | Stratified by family and file type | Report per stratum, not just aggregate |
| Unseen families | Family-disjoint split (no family in both train and test) | Recall drop vs random split reported |
| Temporal holdout | Train ≤ T, test on first-seen > T + 3 months | Performance within agreed tolerance of in-time |
| Contamination | Dedupe by hash, fuzzy hash (ssdeep/TLSH), and packer; check VT-label leakage into features | Zero exact dupes across splits |
| Adversarial robustness | Packing, section padding, benign-import injection, string encryption | Degradation curve reported |
| Calibration | Reliability diagram, ECE | ECE ≤ 0.05, or the score is reported as uncalibrated |
| Inference cost | ms/sample and $/1M samples on stated hardware | Reported |
| **"0 VT detections" claim** | Treat as a *hypothesis*: sample a set of 0-VT detections; confirm via sandbox and manual RE; report the confirmed-malicious fraction with CI | Only confirmed cases count as true positives |

### B. Supply-chain package datasets

| Check | Protocol |
|---|---|
| Provenance | Where, when, and how collected; scripts; registry ToS compliance |
| Licensing | Licence of each package retained; redistribution rights of the dataset |
| Collection authorization | Any private-registry or customer data? If so, written authorization |
| Coverage | Ecosystems × time × package counts |
| Representativeness | Popularity distribution vs registry; malicious/benign ratio |
| Historical depth | Versions per package; first-seen timestamps |
| Label quality | Label source; inter-rater agreement on a 200-sample audit |
| Duplicates | Tarball hash and normalized-content dedupe; typosquat-cluster grouping |
| Version relationships | Package → version graph present? |
| Source/binary availability | Fraction with bundled native code (relevant to F and B) |

**Defensibility vs public data.** Public alternatives exist: the OpenSSF malicious-packages repository, GuardDog rules, and registry takedown logs. The datasets give an advantage only if they contain (a) labels or behaviors not in public feeds, (b) deeper history, or (c) native-code artifacts paired with source. Until audited, **assume no advantage**.
