"""Deterministic verifier and baseline solvers for re_tasks instances.

Baselines bracket task difficulty:

    strings_baseline   static strings + llm_indicators, no decoding
    xor_bruteforce     tries all single-byte XOR keys over the whole file
    family_extractor   what an analyst writes after reversing one sample of
                       the family: finds the config struct and decodes it.
                       It proves every level is solvable without the answer key.
"""

from __future__ import annotations

import re
import struct
from pathlib import Path

from provenance.llm_indicators import CREDENTIAL_PATTERNS, scan_bytes
from re_tasks.generator import ANSWER_FIELDS, FIELDS, MAGIC, SEP, keystream

_HOST_RE = re.compile(rb"[a-z0-9]{8}\.[a-z0-9]{6}\.test")
_CAMPAIGN_RE = re.compile(rb"CMP-[0-9A-F]{8}")
_MUTEX_RE = re.compile(rb"Global\\[A-Za-z0-9]{12}")
_KEY = b"re-task-fingerprint-key-00000000"


def verify(submission: dict, answer: dict) -> dict:
    per_field = {f: submission.get(f) == answer[f] for f in ANSWER_FIELDS}
    return {"score": sum(per_field.values()) / len(per_field), "solved": all(per_field.values()), "fields": per_field}


def _first(pattern: re.Pattern[bytes], data: bytes) -> str | None:
    m = pattern.search(data)
    return m.group().decode() if m else None


def strings_baseline(data: bytes) -> dict:
    report = scan_bytes(data, _KEY)
    endpoint = next((h for hosts in report.endpoints.values() for h in sorted(hosts)), None)
    cred = report.credentials[0] if report.credentials else None
    return {
        "c2_host": _first(_HOST_RE, data),
        "campaign_id": _first(_CAMPAIGN_RE, data),
        "mutex": _first(_MUTEX_RE, data),
        "llm_endpoint": endpoint,
        "llm_model": sorted(report.models)[0] if report.models else None,
        "credential_provider": cred.provider if cred else None,
        "credential_last4": cred.redacted[-4:] if cred else None,
    }


def _parse(plain: bytes) -> dict | None:
    if not plain.startswith(MAGIC + SEP):
        return None
    parts = plain[len(MAGIC) + 1:].split(SEP)
    if len(parts) != len(FIELDS):
        return None
    try:
        values = dict(zip(FIELDS, (p.decode("ascii") for p in parts)))
    except UnicodeDecodeError:
        return None
    cred = values.pop("credential")
    provider = next((p for p, pat in CREDENTIAL_PATTERNS.items() if pat.fullmatch(cred.encode())), None)
    return values | {"credential_provider": provider, "credential_last4": cred[-4:]}


def _empty() -> dict:
    return {f: None for f in ANSWER_FIELDS}


def xor_bruteforce(data: bytes) -> dict:
    for k in range(256):
        x = data.translate(bytes(b ^ k for b in range(256)))
        i = x.find(MAGIC + SEP)
        while i != -1:
            end = i
            seps = 0
            while end < len(x) and (32 <= x[end] < 127 or (x[end] == SEP[0] and seps < len(FIELDS))):
                seps += x[end] == SEP[0]
                end += 1
            if seps == len(FIELDS):
                last_sep = x.rfind(SEP, i, end)
                for j in range(end, last_sep, -1):
                    parsed = _parse(x[i:j])
                    if parsed and parsed["credential_provider"]:
                        return parsed
            i = x.find(MAGIC + SEP, i + 1)
    return _empty()


def family_extractor(data: bytes) -> dict:
    for off in range(0, len(data) - 8):
        key, n = struct.unpack_from("<II", data, off)
        if not 32 <= n <= 1024 or off + 8 + n > len(data):
            continue
        blob = data[off + 8: off + 8 + n]
        for level in (0, 1, 2):
            if level == 1 and key > 255:
                continue
            head = bytes(b ^ k for b, k in zip(blob[:5], keystream(level, key, 5)))
            if head != MAGIC + SEP:
                continue
            plain = bytes(b ^ k for b, k in zip(blob, keystream(level, key, n)))
            parsed = _parse(plain)
            if parsed:
                return parsed
    return _empty()


SOLVERS = {"strings": strings_baseline, "xor_bruteforce": xor_bruteforce, "family_extractor": family_extractor}


def solve_file(path: Path, solver: str) -> dict:
    return SOLVERS[solver](Path(path).read_bytes())
