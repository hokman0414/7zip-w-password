# 7zip-w-password

## AI code provenance / IP code-reuse research

- `research/EXECUTIVE_DECISION.md`: the decision (PIVOT to IP code-reuse investigation, PILOT FIRST) and the supporting analysis in `research/01`–`13`.
- `provenance/`: the vertical slice. It covers keyed source/binary fingerprinting, open-set retrieval, case-gated access, a hash-chained audit log, and evidence reports.
- `bench/`: the synthetic benchmark harness and its measured results (`bench/results/`).

```bash
python3 -m unittest discover -s tests -t .
python3 -m bench.run_benchmark --n-targets 200 --index-size 2000 --out bench/results/quick   # needs gcc, clang, binutils
```
