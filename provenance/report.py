"""Evidence report construction.

Reports show only query-side plaintext for matched features (the investigator
already holds the artifact). Indexed record content is never revealed; the
candidate reference is opaque and must be resolved inside the record owner's
own systems under their own access controls.
"""

from __future__ import annotations

import time

LIMITATIONS = [
    "A match means shared distinctive features, not proof of authorship or of the generating account.",
    "Alternative explanations must be excluded: shared libraries, public code, common templates, "
    "independent generation of similar code by the same or another model, and code copied between users.",
    "Absence of a match is not evidence of absence (stripped/obfuscated binaries, expired records, "
    "or code produced outside indexed systems).",
    "Classifier output, if present, is a model opinion and not ground truth about maliciousness.",
]


def build_report(case, artifact_name, sha256, fs, cands, decision, signal, plaintext) -> dict:
    top_evidence = []
    if decision.top:
        for h in decision.top.matched[:25]:
            top_evidence.append(plaintext.get(h, f"<keyed:{h}>"))
    return {
        "case_id": case.case_id,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "artifact": {"name": artifact_name, "sha256": sha256, "kind": fs.kind, "n_features": len(fs.features)},
        "decision": {
            "escalate": decision.escalate,
            "reason": decision.reason,
            "margin_over_runner_up": round(decision.margin, 3),
        },
        "candidates": [
            {
                "ref": c.ref,
                "score": round(c.score, 3),
                "containment": round(c.containment, 3),
                "matched_by_type": c.matched_by_type,
            }
            for c in cands
        ],
        "top_candidate_evidence": sorted(top_evidence),
        "classifier_signal": {
            "model_id": signal.model_id,
            "score": signal.score,
            "calibrated": signal.calibrated,
            "note": signal.note,
        },
        "limitations": LIMITATIONS,
    }
