# 7zip-w-password

## AI code provenance / IP code-reuse research

- `research/EXECUTIVE_DECISION.md`: the decision (PIVOT to malware-RE training environments and evaluations for frontier labs, with Safeguards SME services, at PILOT FIRST; IP code-reuse investigation as the RESEARCH FIRST fallback) and the supporting analysis in `research/01`–`16`.
- `re_tasks/`: generator for unique, benign malware-like RE task binaries with hidden configs and decoys, a deterministic grader, and baseline solvers.
- `provenance/`: the vertical slice. It covers keyed source/binary fingerprinting, open-set retrieval, case-gated access, a hash-chained audit log, and evidence reports. `llm_indicators.py` extracts indicators of LLM-enabled malware (provider credentials, endpoints, model names, prompts) and clusters samples by shared key. Credentials are kept only in redacted and fingerprinted form and are never validated or used.
- `bench/`: the benchmark harnesses and their measured results (`bench/results/`).

```bash
python3 -m unittest discover -s tests -t .
python3 -m bench.run_benchmark --n-targets 200 --index-size 2000 --out bench/results/quick   # needs gcc, clang, binutils
python3 -m bench.run_llm_indicator_bench --benign-llm-software <dir of unpacked LLM SDK wheels>   # needs gcc
python3 -m bench.run_re_tasks_bench --per-cell 40   # needs gcc
```
