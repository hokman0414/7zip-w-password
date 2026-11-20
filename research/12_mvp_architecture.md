# 12 — MVP Architecture

## Phase 12 repository inventory (as of 2026-11-20)

| Item | Found | Notes |
|---|---|---|
| Existing source files | `README.md` only on `main`. 15 other remote branches hold unrelated projects (stock research, influence research, conference-talk scraping) | Not reusable for this product |
| Model artifacts (malware classifier) | **None** on any branch | Not retrained, not overwritten. Nothing to touch. |
| Training/inference interfaces | **None** | Adapter boundary added: `provenance/classifier.py` |
| Dataset schemas | **None** | — |
| Package ingestion pipelines | **None** | — |
| Existing APIs | **None** | — |
| Tests | **None** before this work | `tests/test_provenance.py` added (9 tests) |
| Dependencies | **None** | The slice is Python 3.10+ stdlib only, plus system `objdump`/`strip`/`gcc`/`clang` for the benchmark |
| Security boundaries | **None** | Implemented in `provenance/service.py` |

**Reusable components from the founder:** none available in-repo. When the classifier is supplied it plugs into `MalwareClassifier` (one method, `score(path) -> ClassifierSignal`). Its output is labelled as model opinion, never as ground truth.

## MVP architecture (for Candidate F, reusing the vertical slice)

```
 IP owner premises (key never leaves)                 Analysis service (owner-hosted or vendor-hosted)
 ┌──────────────────────────────┐                    ┌──────────────────────────────────────────────┐
 │ 1 Source ingestion (CLI)      │  keyed hashes only │ 4 Artifact ingestion (binaries/firmware/apps) │
 │ 3 Source fingerprint extract  │ ─────────────────▶ │ 5 Binary fingerprint extraction (ELF→PE→MachO)│
 │   (strings, consts, symbols,  │                    │ 6 Similarity retrieval (inverted index, IDF)  │
 │    winnow) → HMAC(key, f)     │                    │ 7 Candidate ranking + open-set decision       │
 └──────────────────────────────┘                    │ 8 Evidence reporting (expert packet)          │
                                                      │ 2 Malware-classifier adapter (optional signal)│
                                                      │ 9 Access control + hash-chained audit         │
                                                      │10 Retention/deletion (TTL, per-record delete) │
                                                      │11 Benchmark harness (regression gate)         │
                                                      └──────────────────────────────────────────────┘
```

| # | Component | Status in repo | File(s) | Next increment |
|---|---|---|---|---|
| 1 | Artifact ingestion | Source text and ELF path | `service.py` | Firmware unpacking via BANG-class unpacker; APK/IPA; wheels/npm native addons |
| 2 | Malware classification adapter | Interface + `UnavailableClassifier` | `classifier.py` | Wire the founder model after doc 08 validation |
| 3 | Source fingerprint extraction | C-family strings, constants, calls, function names, winnowing | `features.py` | C++/Java/Go/Rust/Python/JS lexers; library-feature suppression |
| 4 | Binary fingerprint extraction | ELF strings, immediates (±1), imports (aliased), local symbols | `features.py` | PE/Mach-O; ARM; .NET/Java bytecode; decompiler-derived features |
| 5 | Similarity retrieval | Inverted index, keyed hashes, IDF, df cap | `index.py` | Containment-first scoring for partial reuse; sharding |
| 6 | Candidate ranking | Score + distinct-feature + margin gates | `index.py: decide()` | Per-corpus calibration job; lineage grouping |
| 7 | Evidence reporting | JSON report with matched query-side features, limitations | `report.py` | Location-level exhibits (offset ↔ file:line); reproducibility script |
| 8 | Access control + audit | Roles, case-gated queries, query budget, hash-chained audit, deny logging | `service.py` | External identity (OIDC); WORM log storage; dual-control for escalations |
| 9 | Retention/deletion | TTL purge; delete propagates to postings | `index.py`, `service.py` | Scheduled purge; deletion receipts |
| 10 | Benchmark harness | Synthetic corpus, 9 conditions, 6 methods, open-set calibration | `bench/` | X1–X3 real-code benchmarks (doc 09) |

## Security and data-handling rules enforced in code

- Indexed records store only `HMAC-SHA256(key, feature)[:12]` plus type. No plaintext code or strings are stored (unit test `test_keyed_storage_has_no_plaintext`).
- Queries require an investigator role **and** an open case with a documented basis. Each case has a query budget, and denials are audited.
- Reports reveal only the *query-side* plaintext of matched features. Indexed records are referenced by opaque ref only.
- Audit entries form a SHA-256 hash chain, and tampering is detected (`test_audit_chain_detects_tampering`).
- No external network calls. No AI service receives any code, artifact, or record.

## Smallest testable vertical slice (implemented)

Source ingest → keyed index → stripped -O2 binary query → ranked candidates → open-set decision → evidence report → audit verification. This path is covered by `tests/test_provenance.py::ServiceTests::test_end_to_end_binary_investigation` and exercised at scale by `bench/run_benchmark.py`.
