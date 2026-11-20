# 09 — Benchmark Design and Measured Results

## Reproduce

```bash
python3 -m unittest discover -s tests -t .
python3 -m bench.run_benchmark --n-targets 1000 --index-size 10000 --n-ood 400 --n-ip 200 \
    --binary-baseline-refs 2000 --out bench/results/default
python3 -m bench.run_benchmark --n-targets 500 --index-size 10000 --n-ood 400 --n-ip 200 \
    --binary-baseline-refs 600 --common-frac 0.8 --seed 11 --out bench/results/boilerplate_heavy
```

Environment: Python 3.12.3, gcc 13.3.0, clang 18.1.3, x86-64 Linux, 4 vCPU. Wall time: 174 s (default) and 94 s (boilerplate-heavy). Full outputs: `bench/results/*/results.{md,json}`.

## Design

### Corpus (synthetic, benign)

`bench/synth.py` renders C programs from structured specs. Each program has 3–6 functions drawn from 12 benign templates (hashing, CRC, state machines, env parsing, buffers, …), with per-program constants and log strings. A tunable share (`--common-frac`) is drawn from a shared boilerplate pool.

| Target (from tasking) | What was actually built | Gap |
|---|---|---|
| 1,000 AI-generated programs | 1,000 synthetic "generated" programs (default run); 500 (boilerplate run) | **Not real LLM output.** No model was called. |
| 1,000 human-written controls | Not built. Retrieval does not condition on authorship. The **out-of-index** set (400 programs, 800 binaries) serves as the negative control | Real human code not used; would also need licensing |
| 500 AI-assisted / heavily edited | Proxied by: modified-constants (1,000), refactored source (1,000), session-lineage siblings (≈ 30% of targets), IP transplants (200) | Edits are rule-based, not human |
| 10,000 candidate session records | **10,000-record index** (targets + lineage siblings + distractors) | — |

### Toolchains and transforms (all measured)

| Variant | Compiler | Opt | Stripped | Source transform |
|---|---|---|---|---|
| gcc-O0 | gcc 13.3 | -O0 | no | — |
| gcc-O2 | gcc 13.3 | -O2 | no | — |
| gcc-O3-stripped | gcc 13.3 | -O3 | yes | — |
| clang-O2 | clang 18.1 | -O2 | no | — |
| clang-Os-stripped | clang 18.1 | -Os | yes | — |
| modified-constants-stripped | gcc | -O2 | yes | 50% of constants re-randomized |
| obfuscated-strings-stripped | gcc | -O2 | yes | All logged strings XOR-encoded, decoded at runtime |
| obfuscated-strings+modified-constants-stripped | gcc | -O2 | yes | Both of the above (80% constants) |
| ip-transplant | gcc | -O2 | yes | 2 donor functions renamed and embedded in a host with 3 unrelated functions |
| refactored source (source query) | — | — | — | All functions renamed; definition order shuffled |
| **No-match condition** | gcc -O2 and -O3-stripped | | | 400 out-of-index programs never indexed |

**Not tested:** different *versions* of the same compiler (only one gcc and one clang installed), PE/Mach-O, ARM, packers, unseen *model* versions (no model used), Go/Rust/C++.

### Methods compared

| Required baseline | Implementation | Notes |
|---|---|---|
| Exact string matching | `exact-strings` (s: features only) | — |
| Normalized source hashing | SHA-256 of identifier-/literal-abstracted token stream | Source→source only; not applicable to binaries |
| Conventional binary similarity | Opcode-mnemonic 5-gram sets vs **gcc-O0 reference binaries** for 2,000 (default) / 600 (boilerplate) records | Requires reference binaries, which a session index would not hold; generous to the baseline |
| Structural fingerprints | `winnowing-only` (k = 12, w = 8 over abstracted tokens) for source queries; `constants-only`, `symbols-only` ablations | — |
| Embedding-based retrieval | **Not run.** An untrained sparse TF-IDF cosine is reported as a vector-space stand-in | Needs real paired data to train |
| Hybrid retrieval | `hybrid-structural` (strings 1.0, symbols 0.8, constants 0.6, imports 0.1 × IDF; df > 5% ignored) | The slice's default |

### Metrics

Recall@1, Recall@10, MRR, Lineage@1 (top-1 is the target or a sibling from the same session lineage). Open-set metrics:

- **Calibration:** half of the out-of-index programs (both variants) are used to set the score threshold at the 99th percentile of top scores.
- **Gates:** ≥ 3 distinct shared features and margin ≥ 0.
- **False-escalation rate (FER):** measured on the *held-out* half.
- **Escalation recall** and **precision at threshold:** on in-index queries.

Latency is measured separately for search and feature extraction. Storage is reported per record.

## Results (measured, not projected)

### Headline: hybrid method

| Query set | Default R@1 | Default R@10 | Default MRR | Boilerplate-heavy R@10 |
|---|---|---|---|---|
| gcc-O0 | 0.941 | 1.000 | 0.970 | 1.000 |
| gcc-O2 | 0.935 | 1.000 | 0.967 | 1.000 |
| gcc-O3-stripped | 0.932 | 1.000 | 0.965 | 0.912 |
| clang-O2 | 0.927 | 1.000 | 0.962 | 1.000 |
| clang-Os-stripped | 0.919 | 0.999 | 0.957 | 0.894 |
| modified-constants-stripped | 0.927 | 0.999 | 0.961 | 0.858 |
| obfuscated-strings-stripped | 0.828 | 0.992 | 0.902 | 0.812 |
| obfuscated-strings+modified-constants-stripped | 0.530 | 0.768 | 0.630 | 0.348 |
| ip-transplant (stripped) | 0.845 | 1.000 | 0.911 | 0.660 |

Recall@1 < Recall@10 is driven mostly by **session-lineage siblings** ranking first (Lineage@1 = 1.000 for every non-obfuscated default condition). That is a correct-lineage, wrong-turn outcome.

### Baselines (default corpus, Recall@10)

| Query set | exact-strings | constants-only | symbols-only | binary-similarity (mnemonic 5-gram) | sparse cosine | **hybrid** |
|---|---|---|---|---|---|---|
| gcc-O0 | 0.990 | 0.996 | 1.000 | 0.583 | 1.000 | **1.000** |
| gcc-O2 | 0.989 | 0.993 | 1.000 | 0.034 | 1.000 | **1.000** |
| gcc-O3-stripped | 0.989 | 0.993 | 0.000 | 0.033 | 1.000 | **1.000** |
| clang-Os-stripped | 0.984 | 0.983 | 0.000 | 0.009 | 0.999 | **0.999** |
| obfuscated-strings-stripped | 0.329 | 0.992 | 0.000 | 0.029 | 0.992 | **0.992** |
| obf.+modified-constants | 0.333 | 0.659 | 0.000 | 0.011 | 0.771 | **0.768** |
| ip-transplant | 0.885 | 0.925 | 0.000 | 0.015 | 1.000 | **1.000** |

Source→source, refactored (rename + reorder), default corpus: normalized source hash R@1 0.069. Winnowing-only R@10 0.160 (uninformative because templates share structure). Exact-strings R@10 0.996. Hybrid + winnow R@10 1.000. Under boilerplate-heavy: exact-strings R@10 0.744; hybrid + winnow R@10 0.962.

### Open-set (no-match) behaviour, hybrid

| Corpus | Threshold | Held-out FER (n = 400 binaries) | Wrong escalations across all in-index sets |
|---|---|---|---|
| Default | score ≥ 12.0 | **0.000** (95% upper bound ≈ 0.75%) | **0** |
| Boilerplate-heavy | score ≥ 8.5 | **0.000** (≈ 0.75%) | **0** |

### Cost (default, 10,000 records)

| Metric | Value |
|---|---|
| Mean features/record | 116.2 |
| Keyed index storage | 15.3 MB total (≈ 1.53 KB/record) |
| Index build | 10.2 s (single-threaded Python) |
| Binary feature extraction | median 4.5 ms, p95 5.5 ms (small ELF; 3 objdump passes) |
| Search latency, hybrid | median 0.28 ms, p95 0.50 ms |
| Search latency, binary-similarity baseline | median 2.3 ms |
| Per-sample analysis cost | Dominated by extraction; < 10 ms CPU per small binary on 1 vCPU |

## Acceptance targets vs measurement

| Provisional target | Default corpus | Boilerplate-heavy | Status |
|---|---|---|---|
| Recall@10 ≥ 90% on in-index cases | Met for every non-adversarial and single-obfuscation condition; **not met** for strings+constants obfuscation (0.768) | **Not met** for clang-Os-stripped (0.894), modified constants (0.858), obfuscated strings (0.812), IP transplant (0.660), full adversary (0.348) | **Partially met** |
| False-positive escalation ≤ 1% out-of-index | 0/400 | 0/400 | **Met on synthetic negatives** |
| Median retrieval latency < 10 s at 10k | 0.28 ms search + 4.5 ms extraction | similar | **Met by ~3 orders of magnitude** |

These are engineering targets on synthetic data. They do **not** establish customer value or real-world performance.

## Threats to validity

1. **Synthetic distinctiveness.** Random constants and combinatorial log strings are more unique than real LLM code. The boilerplate-heavy run shows the direction and size of the bias: up to 34 points of R@10 on IP transplant.
2. **Template homogeneity.** 12 templates make structure-based methods (winnowing, opcode n-grams) look worse than they would on diverse code.
3. **Same-generator negatives.** Out-of-index programs come from the same generator. Real negatives (other users' similar code, public code) could be *closer* to indexed records and raise FER.
4. **Single platform.** ELF x86-64, C only, one version per compiler.
5. **Obfuscation model is simple.** Single-byte XOR is a weak stand-in. Real packers and crypters remove more, including constants.
6. **No real AI output.** The core premise that real LLM output carries distinctive surviving features is untested.
7. **Threshold calibrated per corpus.** Transfer of thresholds across corpora is untested.

## Next benchmark iterations (falsifiable)

| ID | Experiment | Kill / continue criterion |
|---|---|---|
| X1 | Replace the synthetic corpus with **real proprietary-like code**: e.g., 200 permissively licensed C/C++ libraries treated as "private". Compile into host programs and firmware-style images at -O2/-Os, stripped, gcc and clang, x86-64 and ARM | Continue F if stripped R@10 ≥ 0.80 and FER ≤ 1% with real OSS negatives; stop F's binary path if R@10 < 0.6 |
| X2 | Real negatives: index OSS project A; query binaries of *unrelated* projects sharing libraries | FER ≤ 1% after library-feature suppression |
| X3 | Real LLM outputs (authorized, benign prompts, ≥ 2 models), then compile | Tests the original premise. If R@10 < 0.7 on stripped -O2, close Architecture B for AI provenance permanently |
