"""Reproducible provenance-retrieval benchmark on synthetic benign programs.

Usage:
    python3 -m bench.run_benchmark --n-targets 1000 --index-size 10000 --out bench/results

Every number written by this script is measured on this machine at run time.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import random
import re
import shutil
import statistics
import subprocess
import tempfile
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from bench import synth
from provenance.features import extract_binary, extract_source, normalized_source_tokens
from provenance.index import FingerprintIndex

BINARY_VARIANTS = {
    "gcc-O0": (["gcc", "-O0"], False),
    "gcc-O2": (["gcc", "-O2"], False),
    "gcc-O3-stripped": (["gcc", "-O3"], True),
    "clang-O2": (["clang", "-O2"], False),
    "clang-Os-stripped": (["clang", "-Os"], True),
}
# Source-level perturbations applied before compiling with gcc -O2 -s.
PERTURBED_VARIANTS = (
    "modified-constants-stripped",
    "obfuscated-strings-stripped",
    "obfuscated-strings+modified-constants-stripped",
)

METHODS = {
    "exact-strings": {"s"},
    "constants-only": {"c"},
    "symbols-only": {"f"},
    "hybrid-structural": {"s", "c", "f", "i"},
}


def compile_c(src: str, out: Path, cc: list[str], strip: bool) -> bool:
    r = subprocess.run([*cc, "-w", "-o", str(out), "-x", "c", "-"], input=src, capture_output=True, text=True)
    if r.returncode != 0:
        return False
    if strip:
        subprocess.run(["strip", "-s", str(out)], check=True)
    return True


_MNEM_RE = re.compile(r"^\s+[0-9a-f]+:\s+([a-z][a-z0-9.]*)", re.M)


def mnemonic_ngrams(path: Path, n: int = 5) -> set[str]:
    """Conventional binary-similarity baseline: opcode-mnemonic n-grams over .text."""
    dis = subprocess.run(["objdump", "-d", "--no-show-raw-insn", "-j", ".text", str(path)], capture_output=True, text=True).stdout
    m = _MNEM_RE.findall(dis)
    return {"m:" + hashlib.blake2b(" ".join(m[i : i + n]).encode(), digest_size=8).hexdigest() for i in range(len(m) - n + 1)}


def cosine_search(index: FingerprintIndex, feats: set[str], types: set[str], top_k: int = 10):
    """Sparse TF-IDF cosine (an untrained vector-space stand-in, not a learned embedding)."""
    n = max(1, len(index.records))
    df_cap = max(2, int(n * 0.05))
    q = {index.keyed(f) for f in feats if f.split(":", 1)[0] in types}
    q = {h for h in q if 0 < len(index._postings.get(h, ())) <= df_cap}
    qn = math.sqrt(sum(index.idf(h) ** 2 for h in q)) or 1.0
    dots = defaultdict(float)
    for h in q:
        w = index.idf(h) ** 2
        for ref in index._postings[h]:
            dots[ref] += w
    out = []
    for ref, d in dots.items():
        rn = getattr(index, "_norm_cache", {}).get(ref)
        if rn is None:
            rec = index.records[ref]
            rn = math.sqrt(sum(index.idf(h) ** 2 for h, t in rec.hashed.items() if t in types and len(index._postings[h]) <= df_cap)) or 1.0
            index.__dict__.setdefault("_norm_cache", {})[ref] = rn
        out.append((ref, d / (qn * rn)))
    out.sort(key=lambda kv: kv[1], reverse=True)
    return out[:top_k]


def ranked_refs(index: FingerprintIndex, feats: set[str], types: set[str]):
    t0 = time.perf_counter()
    c = index.search(feats, top_k=10, types=types)
    dt = time.perf_counter() - t0
    return [(x.ref, x.score, len(x.matched)) for x in c], dt


def metrics(rows: list[dict]) -> dict:
    if not rows:
        return {}
    r1 = sum(1 for r in rows if r["rank"] == 1) / len(rows)
    r10 = sum(1 for r in rows if r["rank"] and r["rank"] <= 10) / len(rows)
    mrr = sum(1 / r["rank"] for r in rows if r["rank"]) / len(rows)
    lin1 = sum(1 for r in rows if r["lineage_top1"]) / len(rows)
    return {"n": len(rows), "recall@1": round(r1, 4), "recall@10": round(r10, 4), "mrr": round(mrr, 4), "lineage@1": round(lin1, 4)}


def escalates(top, thr):
    return bool(top) and top[0][1] >= thr["min_score"] and top[0][2] >= thr["min_distinct"] and (
        top[0][1] - (top[1][1] if len(top) > 1 else 0.0)
    ) >= thr["min_margin"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-targets", type=int, default=1000)
    ap.add_argument("--index-size", type=int, default=10000)
    ap.add_argument("--n-ood", type=int, default=400)
    ap.add_argument("--n-ip", type=int, default=200)
    ap.add_argument("--lineage-frac", type=float, default=0.3)
    ap.add_argument("--binary-baseline-refs", type=int, default=2000,
                    help="records compiled at gcc-O0 for the conventional binary-similarity baseline")
    ap.add_argument("--common-frac", type=float, default=synth.COMMON_FRAC,
                    help="share of strings/constants drawn from a shared boilerplate pool")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    ap.add_argument("--out", default="bench/results")
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    synth.COMMON_FRAC = args.common_frac
    work = Path(args.workdir or tempfile.mkdtemp(prefix="provbench-"))
    work.mkdir(parents=True, exist_ok=True)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    t_start = time.time()

    # ---- corpus -------------------------------------------------------------
    targets = [synth.random_program(f"t{i:05d}", rng) for i in range(args.n_targets)]
    lineage: dict[str, str] = {}
    index_specs: dict[str, synth.ProgramSpec] = {}
    for t in targets:
        lineage[t.pid] = t.pid
        if rng.random() < args.lineage_frac:
            prev = t
            versions = []
            for v in range(rng.randint(1, 2)):
                prev = synth.iterate(prev, rng, f"{t.pid}_v{v}")
                versions.append(prev)
            # Sibling iterations from the same session are indexed alongside the
            # ground-truth record and act as hard near-duplicate negatives.
            for v in versions:
                index_specs[v.pid] = v
                lineage[v.pid] = t.pid
        index_specs[t.pid] = t
    n_distract = max(0, args.index_size - len(index_specs))
    for i in range(n_distract):
        d = synth.random_program(f"d{i:05d}", rng)
        index_specs[d.pid] = d
        lineage[d.pid] = d.pid
    ood = [synth.random_program(f"o{i:05d}", rng) for i in range(args.n_ood)]
    ip_cases = []
    for i in range(args.n_ip):
        donor = rng.choice(targets)
        ip_cases.append((synth.transplant(donor, rng, f"ip{i:05d}"), donor.pid))

    # ---- index build (source side, keyed hashes only) ----------------------
    index = FingerprintIndex(key=hashlib.sha256(b"benchmark-index-key").digest())
    t0 = time.perf_counter()
    for pid, spec in index_specs.items():
        index.add(pid, extract_source(synth.render(spec)).features)
    build_s = time.perf_counter() - t0
    feats_per_record = statistics.mean(len(r.hashed) for r in index.records.values())

    # ---- compile queries ---------------------------------------------------
    jobs = []  # (group, variant, query_id, truth_pid, src, cc, strip)
    for t in targets:
        src = synth.render(t)
        for name, (cc, strip) in BINARY_VARIANTS.items():
            jobs.append(("in-index", name, t.pid, t.pid, src, cc, strip))
        jobs.append(("in-index", "modified-constants-stripped", t.pid, t.pid,
                     synth.render(synth.mutate_constants(t, rng)), ["gcc", "-O2"], True))
        jobs.append(("in-index", "obfuscated-strings-stripped", t.pid, t.pid,
                     synth.render(t, obfuscate_strings=True), ["gcc", "-O2"], True))
        jobs.append(("in-index", "obfuscated-strings+modified-constants-stripped", t.pid, t.pid,
                     synth.render(synth.mutate_constants(t, rng, frac=0.8), obfuscate_strings=True), ["gcc", "-O2"], True))
    for o in ood:
        src = synth.render(o)
        jobs.append(("out-of-index", "gcc-O2", o.pid, None, src, ["gcc", "-O2"], False))
        jobs.append(("out-of-index", "gcc-O3-stripped", o.pid, None, src, ["gcc", "-O3"], True))
    for spec, donor in ip_cases:
        jobs.append(("ip-transplant", "gcc-O2-stripped", spec.pid, donor, synth.render(spec), ["gcc", "-O2"], True))

    def run_job(j):
        group, variant, qid, truth, src, cc, strip = j
        path = work / f"{qid}.{variant}.bin"
        ok = compile_c(src, path, cc, strip)
        if not ok:
            return None
        t1 = time.perf_counter()
        fs = extract_binary(path)
        ext = time.perf_counter() - t1
        return {"group": group, "variant": variant, "qid": qid, "truth": truth, "path": str(path),
                "features": fs.features, "extract_s": ext, "size": path.stat().st_size}

    t0 = time.perf_counter()
    with ThreadPoolExecutor(args.workers) as ex:
        compiled = [r for r in ex.map(run_job, jobs) if r]
    compile_extract_s = time.perf_counter() - t0
    failed_compiles = len(jobs) - len(compiled)

    # ---- conventional binary similarity baseline ---------------------------
    # Requires a *reference binary* per record, which a source/session index
    # would not normally hold; included only as a comparison point.
    ref_ids = [t.pid for t in targets] + [p for p in index_specs if p.startswith("d")][: max(0, args.binary_baseline_refs - len(targets))]
    bin_index = FingerprintIndex(key=hashlib.sha256(b"benchmark-binary-key").digest())

    def ref_job(pid):
        path = work / f"{pid}.ref.bin"
        if compile_c(synth.render(index_specs[pid]), path, ["gcc", "-O0"], False):
            return pid, mnemonic_ngrams(path)
        return pid, None

    with ThreadPoolExecutor(args.workers) as ex:
        for pid, grams in ex.map(ref_job, ref_ids):
            if grams:
                bin_index.add(pid, grams)

    # ---- evaluate ----------------------------------------------------------
    results: dict = {"retrieval": {}, "baseline_binary_similarity": {}, "sparse_cosine": {}}
    per_query: list[dict] = []
    latencies = defaultdict(list)
    for q in compiled:
        for method, types in METHODS.items():
            top, dt = ranked_refs(index, q["features"], types)
            latencies[method].append(dt)
            refs = [r for r, _, _ in top]
            rank = refs.index(q["truth"]) + 1 if q["truth"] in refs else None
            per_query.append({
                "group": q["group"], "variant": q["variant"], "method": method, "qid": q["qid"],
                "truth": q["truth"], "rank": rank,
                "lineage_top1": bool(top) and q["truth"] is not None and lineage.get(top[0][0]) == lineage.get(q["truth"]),
                "top": top[:3],
            })
        if q["group"] != "out-of-index":
            cs = cosine_search(index, q["features"], METHODS["hybrid-structural"])
            refs = [r for r, _ in cs]
            rank = refs.index(q["truth"]) + 1 if q["truth"] in refs else None
            results["sparse_cosine"].setdefault(f'{q["group"]}/{q["variant"]}', []).append(
                {"rank": rank, "lineage_top1": bool(cs) and lineage.get(cs[0][0]) == lineage.get(q["truth"])})
            if q["truth"] in bin_index.records:
                t1 = time.perf_counter()
                bc = bin_index.search(mnemonic_ngrams(Path(q["path"])), top_k=10)
                latencies["binary-similarity"].append(time.perf_counter() - t1)
                refs = [c.ref for c in bc]
                rank = refs.index(q["truth"]) + 1 if q["truth"] in refs else None
                results["baseline_binary_similarity"].setdefault(f'{q["group"]}/{q["variant"]}', []).append(
                    {"rank": rank, "lineage_top1": bool(bc) and lineage.get(bc[0].ref) == lineage.get(q["truth"])})

    for k in list(results["sparse_cosine"]):
        results["sparse_cosine"][k] = metrics(results["sparse_cosine"][k])
    for k in list(results["baseline_binary_similarity"]):
        results["baseline_binary_similarity"][k] = metrics(results["baseline_binary_similarity"][k])

    grouped = defaultdict(list)
    for r in per_query:
        if r["group"] != "out-of-index":
            grouped[(r["method"], r["group"], r["variant"])].append(r)
    for (m, g, v), rows in grouped.items():
        results["retrieval"].setdefault(m, {})[f"{g}/{v}"] = metrics(rows)

    # ---- open-set calibration on held-out OOD split ------------------------
    oos = defaultdict(list)
    for r in per_query:
        if r["group"] == "out-of-index":
            oos[r["method"]].append(r)
    open_set = {}
    for method, rows in oos.items():
        ids = sorted({r["qid"] for r in rows})
        calib_ids = set(ids[: len(ids) // 2])
        calib = [r for r in rows if r["qid"] in calib_ids]
        held = [r for r in rows if r["qid"] not in calib_ids]
        tops = sorted((r["top"][0][1] if r["top"] else 0.0) for r in calib)
        q99 = tops[min(len(tops) - 1, int(math.ceil(0.99 * len(tops))) - 1)] if tops else 0.0
        thr = {"min_score": round(q99 + 1e-6, 4), "min_margin": 0.0, "min_distinct": 3}
        fe = sum(1 for r in held if escalates(r["top"], thr)) / max(1, len(held))
        inidx = defaultdict(lambda: {"n": 0, "escalated": 0, "correct": 0, "wrong": 0})
        for r in per_query:
            if r["method"] != method or r["group"] == "out-of-index":
                continue
            key = f'{r["group"]}/{r["variant"]}'
            s = inidx[key]
            s["n"] += 1
            if escalates(r["top"], thr):
                s["escalated"] += 1
                if r["rank"] == 1 or (r["top"] and lineage.get(r["top"][0][0]) == lineage.get(r["truth"])):
                    s["correct"] += 1
                else:
                    s["wrong"] += 1
        for s in inidx.values():
            s["escalation_recall"] = round(s["correct"] / s["n"], 4) if s["n"] else None
            s["precision_at_threshold"] = round(s["correct"] / s["escalated"], 4) if s["escalated"] else None
        open_set[method] = {
            "threshold": thr,
            "calibration_queries": len(calib),
            "heldout_queries": len(held),
            "heldout_false_escalation_rate": round(fe, 4),
            "in_index": dict(inidx),
        }
    results["open_set"] = open_set

    lat = {m: {"median_ms": round(statistics.median(v) * 1000, 3), "p95_ms": round(sorted(v)[int(0.95 * (len(v) - 1))] * 1000, 3)}
           for m, v in latencies.items() if v}
    ext = [q["extract_s"] for q in compiled]
    results["cost"] = {
        "index_records": len(index.records),
        "index_build_seconds": round(build_s, 2),
        "mean_features_per_record": round(feats_per_record, 1),
        "keyed_index_storage_bytes": index.storage_bytes(),
        "storage_bytes_per_record": round(index.storage_bytes() / len(index.records), 1),
        "binary_feature_extraction_median_ms": round(statistics.median(ext) * 1000, 1),
        "binary_feature_extraction_p95_ms": round(sorted(ext)[int(0.95 * (len(ext) - 1))] * 1000, 1),
        "search_latency": lat,
        "compile_and_extract_wall_seconds": round(compile_extract_s, 1),
        "failed_compiles": failed_compiles,
        "binary_baseline_reference_binaries": len(bin_index.records),
    }

    # ---- source-to-source (refactored) baselines ---------------------------
    src_rows = defaultdict(list)
    norm_hash = {}
    for pid, spec in index_specs.items():
        norm_hash.setdefault(hashlib.sha256(" ".join(normalized_source_tokens(synth.render(spec))).encode()).hexdigest(), []).append(pid)
    for t in targets:
        spec2, order = synth.refactor(t, rng)
        src2 = synth.render(spec2, order=order)
        f2 = extract_source(src2).features
        h = hashlib.sha256(" ".join(normalized_source_tokens(src2)).encode()).hexdigest()
        hits = norm_hash.get(h, [])
        src_rows["normalized-source-hash"].append({"rank": 1 if hits and hits[0] == t.pid else None, "lineage_top1": bool(hits) and lineage.get(hits[0]) == t.pid})
        for m, types in {"winnowing-only": {"w"}, "exact-strings": {"s"}, "hybrid-structural+winnow": {"s", "c", "f", "i", "w"}}.items():
            top, _ = ranked_refs(index, f2, types)
            refs = [r for r, _, _ in top]
            src_rows[m].append({"rank": refs.index(t.pid) + 1 if t.pid in refs else None,
                                "lineage_top1": bool(top) and lineage.get(top[0][0]) == t.pid})
    results["source_refactored"] = {m: metrics(rows) for m, rows in src_rows.items()}

    results["config"] = {**vars(args), "workdir": str(work)}
    results["environment"] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "gcc": subprocess.run(["gcc", "--version"], capture_output=True, text=True).stdout.splitlines()[0],
        "clang": subprocess.run(["clang", "--version"], capture_output=True, text=True).stdout.splitlines()[0],
        "cpus": os.cpu_count(),
        "wall_seconds": round(time.time() - t_start, 1),
    }
    (out_dir / "results.json").write_text(json.dumps(results, indent=2, default=str))
    (out_dir / "results.md").write_text(render_markdown(results))
    print(render_markdown(results))
    if not args.workdir:
        shutil.rmtree(work, ignore_errors=True)


def render_markdown(r: dict) -> str:
    L = ["# Benchmark results (measured)", "", f"Environment: `{r['environment']}`", "",
         "## Binary-to-source retrieval, in-index queries", "",
         "| Method | Query set | n | Recall@1 | Recall@10 | MRR | Lineage@1 |", "|---|---|---|---|---|---|---|"]
    for m, sets in r["retrieval"].items():
        for k, v in sorted(sets.items()):
            L.append(f"| {m} | {k} | {v['n']} | {v['recall@1']} | {v['recall@10']} | {v['mrr']} | {v['lineage@1']} |")
    L += ["", "## Sparse TF-IDF cosine (untrained vector baseline, hybrid features)", "",
          "| Query set | n | Recall@1 | Recall@10 | MRR |", "|---|---|---|---|---|"]
    for k, v in sorted(r["sparse_cosine"].items()):
        L.append(f"| {k} | {v['n']} | {v['recall@1']} | {v['recall@10']} | {v['mrr']} |")
    L += ["", "## Conventional binary similarity (mnemonic 5-grams vs gcc-O0 reference binaries)", "",
          "| Query set | n | Recall@1 | Recall@10 | MRR |", "|---|---|---|---|---|"]
    for k, v in sorted(r["baseline_binary_similarity"].items()):
        L.append(f"| {k} | {v['n']} | {v['recall@1']} | {v['recall@10']} | {v['mrr']} |")
    L += ["", "## Open-set behaviour (threshold calibrated to <=1% false escalation on a calibration split)", ""]
    for m, o in r["open_set"].items():
        L.append(f"### {m}")
        L.append(f"- threshold: `{o['threshold']}`; held-out out-of-index false-escalation rate: **{o['heldout_false_escalation_rate']}** (n={o['heldout_queries']})")
        L.append("")
        L.append("| Query set | n | escalated | correct | wrong | escalation recall | precision@threshold |")
        L.append("|---|---|---|---|---|---|---|")
        for k, s in sorted(o["in_index"].items()):
            L.append(f"| {k} | {s['n']} | {s['escalated']} | {s['correct']} | {s['wrong']} | {s['escalation_recall']} | {s['precision_at_threshold']} |")
        L.append("")
    L += ["## Source-to-source (identifiers renamed + functions reordered)", "",
          "| Method | n | Recall@1 | Recall@10 | MRR |", "|---|---|---|---|---|"]
    for m, v in r["source_refactored"].items():
        L.append(f"| {m} | {v['n']} | {v['recall@1']} | {v['recall@10']} | {v['mrr']} |")
    L += ["", "## Cost", "", "```json", json.dumps(r["cost"], indent=2), "```", ""]
    return "\n".join(L)


if __name__ == "__main__":
    main()
