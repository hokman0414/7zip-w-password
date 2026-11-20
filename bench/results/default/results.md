# Benchmark results (measured)

Environment: `{'python': '3.12.3', 'platform': 'Linux-6.12.113+-x86_64-with-glibc2.39', 'gcc': 'gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0', 'clang': 'Ubuntu clang version 18.1.3 (1ubuntu1)', 'cpus': 4, 'wall_seconds': 173.8}`

## Binary-to-source retrieval, in-index queries

| Method | Query set | n | Recall@1 | Recall@10 | MRR | Lineage@1 |
|---|---|---|---|---|---|---|
| exact-strings | in-index/clang-O2 | 1000 | 0.898 | 0.984 | 0.938 | 0.972 |
| exact-strings | in-index/clang-Os-stripped | 1000 | 0.899 | 0.984 | 0.9385 | 0.972 |
| exact-strings | in-index/gcc-O0 | 1000 | 0.924 | 0.99 | 0.9557 | 0.984 |
| exact-strings | in-index/gcc-O2 | 1000 | 0.917 | 0.989 | 0.9514 | 0.982 |
| exact-strings | in-index/gcc-O3-stripped | 1000 | 0.916 | 0.989 | 0.9509 | 0.982 |
| exact-strings | in-index/modified-constants-stripped | 1000 | 0.914 | 0.988 | 0.9493 | 0.981 |
| exact-strings | in-index/obfuscated-strings+modified-constants-stripped | 1000 | 0.223 | 0.333 | 0.2728 | 0.256 |
| exact-strings | in-index/obfuscated-strings-stripped | 1000 | 0.22 | 0.329 | 0.2695 | 0.253 |
| exact-strings | ip-transplant/gcc-O2-stripped | 200 | 0.665 | 0.885 | 0.7548 | 0.755 |
| constants-only | in-index/clang-O2 | 1000 | 0.8 | 0.983 | 0.8812 | 0.96 |
| constants-only | in-index/clang-Os-stripped | 1000 | 0.803 | 0.983 | 0.883 | 0.966 |
| constants-only | in-index/gcc-O0 | 1000 | 0.83 | 0.996 | 0.9032 | 0.994 |
| constants-only | in-index/gcc-O2 | 1000 | 0.818 | 0.993 | 0.8957 | 0.983 |
| constants-only | in-index/gcc-O3-stripped | 1000 | 0.817 | 0.993 | 0.895 | 0.983 |
| constants-only | in-index/modified-constants-stripped | 1000 | 0.706 | 0.927 | 0.8015 | 0.851 |
| constants-only | in-index/obfuscated-strings+modified-constants-stripped | 1000 | 0.386 | 0.659 | 0.4942 | 0.46 |
| constants-only | in-index/obfuscated-strings-stripped | 1000 | 0.816 | 0.992 | 0.8939 | 0.981 |
| constants-only | ip-transplant/gcc-O2-stripped | 200 | 0.7 | 0.925 | 0.7892 | 0.825 |
| symbols-only | in-index/clang-O2 | 1000 | 0.834 | 1.0 | 0.9072 | 1.0 |
| symbols-only | in-index/clang-Os-stripped | 1000 | 0.0 | 0.0 | 0.0 | 0.0 |
| symbols-only | in-index/gcc-O0 | 1000 | 0.834 | 1.0 | 0.9072 | 1.0 |
| symbols-only | in-index/gcc-O2 | 1000 | 0.834 | 1.0 | 0.9072 | 1.0 |
| symbols-only | in-index/gcc-O3-stripped | 1000 | 0.0 | 0.0 | 0.0 | 0.0 |
| symbols-only | in-index/modified-constants-stripped | 1000 | 0.0 | 0.0 | 0.0 | 0.0 |
| symbols-only | in-index/obfuscated-strings+modified-constants-stripped | 1000 | 0.0 | 0.0 | 0.0 | 0.0 |
| symbols-only | in-index/obfuscated-strings-stripped | 1000 | 0.0 | 0.0 | 0.0 | 0.0 |
| symbols-only | ip-transplant/gcc-O2-stripped | 200 | 0.0 | 0.0 | 0.0 | 0.0 |
| hybrid-structural | in-index/clang-O2 | 1000 | 0.927 | 1.0 | 0.9623 | 1.0 |
| hybrid-structural | in-index/clang-Os-stripped | 1000 | 0.919 | 0.999 | 0.9571 | 0.996 |
| hybrid-structural | in-index/gcc-O0 | 1000 | 0.941 | 1.0 | 0.97 | 1.0 |
| hybrid-structural | in-index/gcc-O2 | 1000 | 0.935 | 1.0 | 0.9668 | 1.0 |
| hybrid-structural | in-index/gcc-O3-stripped | 1000 | 0.932 | 1.0 | 0.9652 | 1.0 |
| hybrid-structural | in-index/modified-constants-stripped | 1000 | 0.927 | 0.999 | 0.9613 | 0.995 |
| hybrid-structural | in-index/obfuscated-strings+modified-constants-stripped | 1000 | 0.53 | 0.768 | 0.6295 | 0.619 |
| hybrid-structural | in-index/obfuscated-strings-stripped | 1000 | 0.828 | 0.992 | 0.9019 | 0.983 |
| hybrid-structural | ip-transplant/gcc-O2-stripped | 200 | 0.845 | 1.0 | 0.911 | 0.95 |

## Sparse TF-IDF cosine (untrained vector baseline, hybrid features)

| Query set | n | Recall@1 | Recall@10 | MRR |
|---|---|---|---|---|
| in-index/clang-O2 | 1000 | 0.984 | 1.0 | 0.9917 |
| in-index/clang-Os-stripped | 1000 | 0.982 | 0.999 | 0.99 |
| in-index/gcc-O0 | 1000 | 0.991 | 1.0 | 0.9955 |
| in-index/gcc-O2 | 1000 | 0.988 | 1.0 | 0.994 |
| in-index/gcc-O3-stripped | 1000 | 0.988 | 1.0 | 0.994 |
| in-index/modified-constants-stripped | 1000 | 0.986 | 1.0 | 0.9923 |
| in-index/obfuscated-strings+modified-constants-stripped | 1000 | 0.586 | 0.771 | 0.6617 |
| in-index/obfuscated-strings-stripped | 1000 | 0.925 | 0.992 | 0.9562 |
| ip-transplant/gcc-O2-stripped | 200 | 0.925 | 1.0 | 0.9608 |

## Conventional binary similarity (mnemonic 5-grams vs gcc-O0 reference binaries)

| Query set | n | Recall@1 | Recall@10 | MRR |
|---|---|---|---|---|
| in-index/clang-O2 | 1000 | 0.002 | 0.007 | 0.0035 |
| in-index/clang-Os-stripped | 1000 | 0.002 | 0.009 | 0.0035 |
| in-index/gcc-O0 | 1000 | 0.376 | 0.583 | 0.4434 |
| in-index/gcc-O2 | 1000 | 0.007 | 0.034 | 0.0126 |
| in-index/gcc-O3-stripped | 1000 | 0.007 | 0.033 | 0.0124 |
| in-index/modified-constants-stripped | 1000 | 0.002 | 0.02 | 0.0059 |
| in-index/obfuscated-strings+modified-constants-stripped | 1000 | 0.0 | 0.011 | 0.0019 |
| in-index/obfuscated-strings-stripped | 1000 | 0.008 | 0.029 | 0.0116 |
| ip-transplant/gcc-O2-stripped | 200 | 0.005 | 0.015 | 0.0067 |

## Open-set behaviour (threshold calibrated to <=1% false escalation on a calibration split)

### exact-strings
- threshold: `{'min_score': 12.0009, 'min_margin': 0.0, 'min_distinct': 3}`; held-out out-of-index false-escalation rate: **0.0** (n=400)

| Query set | n | escalated | correct | wrong | escalation recall | precision@threshold |
|---|---|---|---|---|---|---|
| in-index/clang-O2 | 1000 | 865 | 865 | 0 | 0.865 | 1.0 |
| in-index/clang-Os-stripped | 1000 | 865 | 865 | 0 | 0.865 | 1.0 |
| in-index/gcc-O0 | 1000 | 911 | 911 | 0 | 0.911 | 1.0 |
| in-index/gcc-O2 | 1000 | 896 | 896 | 0 | 0.896 | 1.0 |
| in-index/gcc-O3-stripped | 1000 | 896 | 896 | 0 | 0.896 | 1.0 |
| in-index/modified-constants-stripped | 1000 | 894 | 894 | 0 | 0.894 | 1.0 |
| in-index/obfuscated-strings+modified-constants-stripped | 1000 | 7 | 7 | 0 | 0.007 | 1.0 |
| in-index/obfuscated-strings-stripped | 1000 | 7 | 7 | 0 | 0.007 | 1.0 |
| ip-transplant/gcc-O2-stripped | 200 | 80 | 80 | 0 | 0.4 | 1.0 |

### constants-only
- threshold: `{'min_score': 5.1104, 'min_margin': 0.0, 'min_distinct': 3}`; held-out out-of-index false-escalation rate: **0.0** (n=400)

| Query set | n | escalated | correct | wrong | escalation recall | precision@threshold |
|---|---|---|---|---|---|---|
| in-index/clang-O2 | 1000 | 819 | 819 | 0 | 0.819 | 1.0 |
| in-index/clang-Os-stripped | 1000 | 817 | 817 | 0 | 0.817 | 1.0 |
| in-index/gcc-O0 | 1000 | 946 | 946 | 0 | 0.946 | 1.0 |
| in-index/gcc-O2 | 1000 | 879 | 879 | 0 | 0.879 | 1.0 |
| in-index/gcc-O3-stripped | 1000 | 879 | 879 | 0 | 0.879 | 1.0 |
| in-index/modified-constants-stripped | 1000 | 484 | 484 | 0 | 0.484 | 1.0 |
| in-index/obfuscated-strings+modified-constants-stripped | 1000 | 101 | 101 | 0 | 0.101 | 1.0 |
| in-index/obfuscated-strings-stripped | 1000 | 876 | 876 | 0 | 0.876 | 1.0 |
| ip-transplant/gcc-O2-stripped | 200 | 82 | 82 | 0 | 0.41 | 1.0 |

### symbols-only
- threshold: `{'min_score': 6.8138, 'min_margin': 0.0, 'min_distinct': 3}`; held-out out-of-index false-escalation rate: **0.0** (n=400)

| Query set | n | escalated | correct | wrong | escalation recall | precision@threshold |
|---|---|---|---|---|---|---|
| in-index/clang-O2 | 1000 | 1000 | 1000 | 0 | 1.0 | 1.0 |
| in-index/clang-Os-stripped | 1000 | 0 | 0 | 0 | 0.0 | None |
| in-index/gcc-O0 | 1000 | 1000 | 1000 | 0 | 1.0 | 1.0 |
| in-index/gcc-O2 | 1000 | 1000 | 1000 | 0 | 1.0 | 1.0 |
| in-index/gcc-O3-stripped | 1000 | 0 | 0 | 0 | 0.0 | None |
| in-index/modified-constants-stripped | 1000 | 0 | 0 | 0 | 0.0 | None |
| in-index/obfuscated-strings+modified-constants-stripped | 1000 | 0 | 0 | 0 | 0.0 | None |
| in-index/obfuscated-strings-stripped | 1000 | 0 | 0 | 0 | 0.0 | None |
| ip-transplant/gcc-O2-stripped | 200 | 0 | 0 | 0 | 0.0 | None |

### hybrid-structural
- threshold: `{'min_score': 12.0009, 'min_margin': 0.0, 'min_distinct': 3}`; held-out out-of-index false-escalation rate: **0.0** (n=400)

| Query set | n | escalated | correct | wrong | escalation recall | precision@threshold |
|---|---|---|---|---|---|---|
| in-index/clang-O2 | 1000 | 1000 | 1000 | 0 | 1.0 | 1.0 |
| in-index/clang-Os-stripped | 1000 | 987 | 987 | 0 | 0.987 | 1.0 |
| in-index/gcc-O0 | 1000 | 1000 | 1000 | 0 | 1.0 | 1.0 |
| in-index/gcc-O2 | 1000 | 1000 | 1000 | 0 | 1.0 | 1.0 |
| in-index/gcc-O3-stripped | 1000 | 991 | 991 | 0 | 0.991 | 1.0 |
| in-index/modified-constants-stripped | 1000 | 974 | 974 | 0 | 0.974 | 1.0 |
| in-index/obfuscated-strings+modified-constants-stripped | 1000 | 200 | 200 | 0 | 0.2 | 1.0 |
| in-index/obfuscated-strings-stripped | 1000 | 907 | 907 | 0 | 0.907 | 1.0 |
| ip-transplant/gcc-O2-stripped | 200 | 176 | 176 | 0 | 0.88 | 1.0 |

## Source-to-source (identifiers renamed + functions reordered)

| Method | n | Recall@1 | Recall@10 | MRR |
|---|---|---|---|---|
| normalized-source-hash | 1000 | 0.069 | 0.069 | 0.069 |
| winnowing-only | 1000 | 0.039 | 0.16 | 0.0712 |
| exact-strings | 1000 | 0.938 | 0.996 | 0.9661 |
| hybrid-structural+winnow | 1000 | 0.948 | 1.0 | 0.9735 |

## Cost

```json
{
  "index_records": 10000,
  "index_build_seconds": 10.16,
  "mean_features_per_record": 116.2,
  "keyed_index_storage_bytes": 15332106,
  "storage_bytes_per_record": 1533.2,
  "binary_feature_extraction_median_ms": 4.5,
  "binary_feature_extraction_p95_ms": 5.5,
  "search_latency": {
    "exact-strings": {
      "median_ms": 0.194,
      "p95_ms": 0.453
    },
    "constants-only": {
      "median_ms": 0.086,
      "p95_ms": 0.155
    },
    "symbols-only": {
      "median_ms": 0.011,
      "p95_ms": 0.051
    },
    "hybrid-structural": {
      "median_ms": 0.278,
      "p95_ms": 0.496
    },
    "binary-similarity": {
      "median_ms": 2.323,
      "p95_ms": 2.971
    }
  },
  "compile_and_extract_wall_seconds": 117.6,
  "failed_compiles": 0,
  "binary_baseline_reference_binaries": 2000
}
```
