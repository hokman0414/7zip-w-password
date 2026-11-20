# 7zip-w-password

## AI code provenance / IP code-reuse research

- `research/EXECUTIVE_DECISION.md`: the decision and the supporting analysis in `research/01`–`19`. The current decision is PIVOT: do malware-RE expert work now as income, and take adversarial-robustness testing of AI malware-analysis pipelines to PILOT FIRST. The Cycle 7 independent evaluator was found to be already offered by others.
- `re_tasks/`: generator for unique, benign malware-like RE task binaries with hidden configs and decoys, a deterministic grader, and baseline solvers. `evaluate.py` adds evaluator controls: Wilson confidence intervals, a significance gate, per-bank canary strings, and disjoint per-customer partitions. `injection.py` plants AI-analysis-evasion text into those binaries, detects such text statically, and scores any analyzer's verdict flips (refusals count as misses).
- `provenance/`: the vertical slice. It covers keyed source/binary fingerprinting, open-set retrieval, case-gated access, a hash-chained audit log, and evidence reports. `llm_indicators.py` extracts indicators of LLM-enabled malware (provider credentials, endpoints, model names, prompts) and clusters samples by shared key. Credentials are kept only in redacted and fingerprinted form and are never validated or used. `incident_packet.py` turns victim-consented incident artifacts into pseudonymised, provider-neutral evidence packets, one per AI provider.
- `bench/`: the benchmark harnesses and their measured results (`bench/results/`).

```bash
python3 -m unittest discover -s tests -t .
python3 -m bench.run_benchmark --n-targets 200 --index-size 2000 --out bench/results/quick   # needs gcc, clang, binutils
python3 -m bench.run_llm_indicator_bench --benign-llm-software <dir of unpacked LLM SDK wheels>   # needs gcc
python3 -m bench.run_re_tasks_bench --per-cell 40   # needs gcc
python3 -m bench.run_incident_packet_bench   # synthetic incidents only
python3 -m bench.run_re_eval_report --per-level 60   # needs gcc
python3 -m bench.run_injection_bench --seeds 2   # needs gcc; no LLM is called
```
