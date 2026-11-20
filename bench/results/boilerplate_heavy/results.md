# Benchmark results (measured)

Environment: `{'python': '3.12.3', 'platform': 'Linux-6.12.113+-x86_64-with-glibc2.39', 'gcc': 'gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0', 'clang': 'Ubuntu clang version 18.1.3 (1ubuntu1)', 'cpus': 4, 'wall_seconds': 94.1}`

## Binary-to-source retrieval, in-index queries

| Method | Query set | n | Recall@1 | Recall@10 | MRR | Lineage@1 |
|---|---|---|---|---|---|---|
| exact-strings | in-index/clang-O2 | 500 | 0.57 | 0.692 | 0.6246 | 0.65 |
| exact-strings | in-index/clang-Os-stripped | 500 | 0.572 | 0.692 | 0.6256 | 0.65 |
| exact-strings | in-index/gcc-O0 | 500 | 0.598 | 0.72 | 0.6523 | 0.678 |
| exact-strings | in-index/gcc-O2 | 500 | 0.588 | 0.712 | 0.6433 | 0.67 |
| exact-strings | in-index/gcc-O3-stripped | 500 | 0.59 | 0.712 | 0.6443 | 0.67 |
| exact-strings | in-index/modified-constants-stripped | 500 | 0.586 | 0.712 | 0.6426 | 0.67 |
| exact-strings | in-index/obfuscated-strings+modified-constants-stripped | 500 | 0.086 | 0.124 | 0.1018 | 0.108 |
| exact-strings | in-index/obfuscated-strings-stripped | 500 | 0.082 | 0.12 | 0.0978 | 0.104 |
| exact-strings | ip-transplant/gcc-O2-stripped | 200 | 0.305 | 0.385 | 0.3355 | 0.335 |
| constants-only | in-index/clang-O2 | 500 | 0.58 | 0.746 | 0.6532 | 0.706 |
| constants-only | in-index/clang-Os-stripped | 500 | 0.582 | 0.742 | 0.654 | 0.72 |
| constants-only | in-index/gcc-O0 | 500 | 0.696 | 0.862 | 0.7708 | 0.852 |
| constants-only | in-index/gcc-O2 | 500 | 0.628 | 0.79 | 0.7003 | 0.774 |
| constants-only | in-index/gcc-O3-stripped | 500 | 0.626 | 0.79 | 0.6993 | 0.772 |
| constants-only | in-index/modified-constants-stripped | 500 | 0.424 | 0.548 | 0.479 | 0.51 |
| constants-only | in-index/obfuscated-strings+modified-constants-stripped | 500 | 0.154 | 0.252 | 0.1971 | 0.196 |
| constants-only | in-index/obfuscated-strings-stripped | 500 | 0.626 | 0.79 | 0.6997 | 0.772 |
| constants-only | ip-transplant/gcc-O2-stripped | 200 | 0.355 | 0.5 | 0.4208 | 0.465 |
| symbols-only | in-index/clang-O2 | 500 | 0.806 | 1.0 | 0.894 | 1.0 |
| symbols-only | in-index/clang-Os-stripped | 500 | 0.0 | 0.0 | 0.0 | 0.0 |
| symbols-only | in-index/gcc-O0 | 500 | 0.806 | 1.0 | 0.894 | 1.0 |
| symbols-only | in-index/gcc-O2 | 500 | 0.806 | 1.0 | 0.894 | 1.0 |
| symbols-only | in-index/gcc-O3-stripped | 500 | 0.0 | 0.0 | 0.0 | 0.0 |
| symbols-only | in-index/modified-constants-stripped | 500 | 0.0 | 0.0 | 0.0 | 0.0 |
| symbols-only | in-index/obfuscated-strings+modified-constants-stripped | 500 | 0.0 | 0.0 | 0.0 | 0.0 |
| symbols-only | in-index/obfuscated-strings-stripped | 500 | 0.0 | 0.0 | 0.0 | 0.0 |
| symbols-only | ip-transplant/gcc-O2-stripped | 200 | 0.0 | 0.0 | 0.0 | 0.0 |
| hybrid-structural | in-index/clang-O2 | 500 | 0.848 | 1.0 | 0.917 | 1.0 |
| hybrid-structural | in-index/clang-Os-stripped | 500 | 0.758 | 0.894 | 0.8192 | 0.884 |
| hybrid-structural | in-index/gcc-O0 | 500 | 0.85 | 1.0 | 0.918 | 1.0 |
| hybrid-structural | in-index/gcc-O2 | 500 | 0.848 | 1.0 | 0.917 | 1.0 |
| hybrid-structural | in-index/gcc-O3-stripped | 500 | 0.776 | 0.912 | 0.8375 | 0.904 |
| hybrid-structural | in-index/modified-constants-stripped | 500 | 0.728 | 0.858 | 0.7872 | 0.836 |
| hybrid-structural | in-index/obfuscated-strings+modified-constants-stripped | 500 | 0.234 | 0.348 | 0.2828 | 0.292 |
| hybrid-structural | in-index/obfuscated-strings-stripped | 500 | 0.648 | 0.812 | 0.7212 | 0.79 |
| hybrid-structural | ip-transplant/gcc-O2-stripped | 200 | 0.48 | 0.66 | 0.5582 | 0.575 |

## Sparse TF-IDF cosine (untrained vector baseline, hybrid features)

| Query set | n | Recall@1 | Recall@10 | MRR |
|---|---|---|---|---|
| in-index/clang-O2 | 500 | 0.96 | 1.0 | 0.9787 |
| in-index/clang-Os-stripped | 500 | 0.864 | 0.904 | 0.8813 |
| in-index/gcc-O0 | 500 | 0.962 | 1.0 | 0.9797 |
| in-index/gcc-O2 | 500 | 0.96 | 1.0 | 0.9787 |
| in-index/gcc-O3-stripped | 500 | 0.884 | 0.92 | 0.9001 |
| in-index/modified-constants-stripped | 500 | 0.81 | 0.868 | 0.8356 |
| in-index/obfuscated-strings+modified-constants-stripped | 500 | 0.278 | 0.348 | 0.3097 |
| in-index/obfuscated-strings-stripped | 500 | 0.746 | 0.814 | 0.778 |
| ip-transplant/gcc-O2-stripped | 200 | 0.575 | 0.66 | 0.611 |

## Conventional binary similarity (mnemonic 5-grams vs gcc-O0 reference binaries)

| Query set | n | Recall@1 | Recall@10 | MRR |
|---|---|---|---|---|
| in-index/clang-O2 | 500 | 0.002 | 0.01 | 0.0041 |
| in-index/clang-Os-stripped | 500 | 0.004 | 0.026 | 0.0087 |
| in-index/gcc-O0 | 500 | 0.55 | 0.764 | 0.6153 |
| in-index/gcc-O2 | 500 | 0.008 | 0.046 | 0.016 |
| in-index/gcc-O3-stripped | 500 | 0.006 | 0.042 | 0.0142 |
| in-index/modified-constants-stripped | 500 | 0.008 | 0.038 | 0.0146 |
| in-index/obfuscated-strings+modified-constants-stripped | 500 | 0.004 | 0.028 | 0.0084 |
| in-index/obfuscated-strings-stripped | 500 | 0.006 | 0.054 | 0.0169 |
| ip-transplant/gcc-O2-stripped | 200 | 0.0 | 0.025 | 0.0062 |

## Open-set behaviour (threshold calibrated to <=1% false escalation on a calibration split)

### exact-strings
- threshold: `{'min_score': 8.5173, 'min_margin': 0.0, 'min_distinct': 3}`; held-out out-of-index false-escalation rate: **0.0** (n=400)

| Query set | n | escalated | correct | wrong | escalation recall | precision@threshold |
|---|---|---|---|---|---|---|
| in-index/clang-O2 | 500 | 90 | 90 | 0 | 0.18 | 1.0 |
| in-index/clang-Os-stripped | 500 | 90 | 90 | 0 | 0.18 | 1.0 |
| in-index/gcc-O0 | 500 | 106 | 106 | 0 | 0.212 | 1.0 |
| in-index/gcc-O2 | 500 | 100 | 100 | 0 | 0.2 | 1.0 |
| in-index/gcc-O3-stripped | 500 | 100 | 100 | 0 | 0.2 | 1.0 |
| in-index/modified-constants-stripped | 500 | 101 | 101 | 0 | 0.202 | 1.0 |
| in-index/obfuscated-strings+modified-constants-stripped | 500 | 1 | 1 | 0 | 0.002 | 1.0 |
| in-index/obfuscated-strings-stripped | 500 | 0 | 0 | 0 | 0.0 | None |
| ip-transplant/gcc-O2-stripped | 200 | 4 | 4 | 0 | 0.02 | 1.0 |

### constants-only
- threshold: `{'min_score': 5.1104, 'min_margin': 0.0, 'min_distinct': 3}`; held-out out-of-index false-escalation rate: **0.0** (n=400)

| Query set | n | escalated | correct | wrong | escalation recall | precision@threshold |
|---|---|---|---|---|---|---|
| in-index/clang-O2 | 500 | 95 | 95 | 0 | 0.19 | 1.0 |
| in-index/clang-Os-stripped | 500 | 94 | 94 | 0 | 0.188 | 1.0 |
| in-index/gcc-O0 | 500 | 163 | 163 | 0 | 0.326 | 1.0 |
| in-index/gcc-O2 | 500 | 113 | 113 | 0 | 0.226 | 1.0 |
| in-index/gcc-O3-stripped | 500 | 113 | 113 | 0 | 0.226 | 1.0 |
| in-index/modified-constants-stripped | 500 | 24 | 24 | 0 | 0.048 | 1.0 |
| in-index/obfuscated-strings+modified-constants-stripped | 500 | 0 | 0 | 0 | 0.0 | None |
| in-index/obfuscated-strings-stripped | 500 | 113 | 113 | 0 | 0.226 | 1.0 |
| ip-transplant/gcc-O2-stripped | 200 | 4 | 4 | 0 | 0.02 | 1.0 |

### symbols-only
- threshold: `{'min_score': 6.8138, 'min_margin': 0.0, 'min_distinct': 3}`; held-out out-of-index false-escalation rate: **0.0** (n=400)

| Query set | n | escalated | correct | wrong | escalation recall | precision@threshold |
|---|---|---|---|---|---|---|
| in-index/clang-O2 | 500 | 500 | 500 | 0 | 1.0 | 1.0 |
| in-index/clang-Os-stripped | 500 | 0 | 0 | 0 | 0.0 | None |
| in-index/gcc-O0 | 500 | 500 | 500 | 0 | 1.0 | 1.0 |
| in-index/gcc-O2 | 500 | 500 | 500 | 0 | 1.0 | 1.0 |
| in-index/gcc-O3-stripped | 500 | 0 | 0 | 0 | 0.0 | None |
| in-index/modified-constants-stripped | 500 | 0 | 0 | 0 | 0.0 | None |
| in-index/obfuscated-strings+modified-constants-stripped | 500 | 0 | 0 | 0 | 0.0 | None |
| in-index/obfuscated-strings-stripped | 500 | 0 | 0 | 0 | 0.0 | None |
| ip-transplant/gcc-O2-stripped | 200 | 0 | 0 | 0 | 0.0 | None |

### hybrid-structural
- threshold: `{'min_score': 8.5173, 'min_margin': 0.0, 'min_distinct': 3}`; held-out out-of-index false-escalation rate: **0.0** (n=400)

| Query set | n | escalated | correct | wrong | escalation recall | precision@threshold |
|---|---|---|---|---|---|---|
| in-index/clang-O2 | 500 | 500 | 500 | 0 | 1.0 | 1.0 |
| in-index/clang-Os-stripped | 500 | 263 | 263 | 0 | 0.526 | 1.0 |
| in-index/gcc-O0 | 500 | 500 | 500 | 0 | 1.0 | 1.0 |
| in-index/gcc-O2 | 500 | 500 | 500 | 0 | 1.0 | 1.0 |
| in-index/gcc-O3-stripped | 500 | 291 | 291 | 0 | 0.582 | 1.0 |
| in-index/modified-constants-stripped | 500 | 204 | 204 | 0 | 0.408 | 1.0 |
| in-index/obfuscated-strings+modified-constants-stripped | 500 | 5 | 5 | 0 | 0.01 | 1.0 |
| in-index/obfuscated-strings-stripped | 500 | 136 | 136 | 0 | 0.272 | 1.0 |
| ip-transplant/gcc-O2-stripped | 200 | 27 | 27 | 0 | 0.135 | 1.0 |

## Source-to-source (identifiers renamed + functions reordered)

| Method | n | Recall@1 | Recall@10 | MRR |
|---|---|---|---|---|
| normalized-source-hash | 500 | 0.068 | 0.068 | 0.068 |
| winnowing-only | 500 | 0.048 | 0.162 | 0.0772 |
| exact-strings | 500 | 0.616 | 0.744 | 0.6736 |
| hybrid-structural+winnow | 500 | 0.82 | 0.962 | 0.882 |

## Cost

```json
{
  "index_records": 10000,
  "index_build_seconds": 9.87,
  "mean_features_per_record": 113.1,
  "keyed_index_storage_bytes": 14926813,
  "storage_bytes_per_record": 1492.7,
  "binary_feature_extraction_median_ms": 4.5,
  "binary_feature_extraction_p95_ms": 5.4,
  "search_latency": {
    "exact-strings": {
      "median_ms": 0.139,
      "p95_ms": 0.376
    },
    "constants-only": {
      "median_ms": 0.06,
      "p95_ms": 0.118
    },
    "symbols-only": {
      "median_ms": 0.011,
      "p95_ms": 0.052
    },
    "hybrid-structural": {
      "median_ms": 0.183,
      "p95_ms": 0.395
    },
    "binary-similarity": {
      "median_ms": 2.378,
      "p95_ms": 3.153
    }
  },
  "compile_and_extract_wall_seconds": 63.5,
  "failed_compiles": 0,
  "binary_baseline_reference_binaries": 600
}
```
