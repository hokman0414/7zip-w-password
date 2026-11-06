"""Optional LLM executor for assignments (OpenAI-compatible chat API, key from OPENAI_API_KEY).

The LLM only reviews the rule-based outcome against the assignment's own evidence slice. It may downgrade a vote or
change it, but any YES it returns must cite evidence ids that exist in the slice; otherwise the rule-based outcome is
kept. Without a key this adapter is not constructed and results are labeled `rule-based`.
"""
from __future__ import annotations

import json

import httpx

from .assignments import Outcome
from .context import SliceView
from .models import AssignmentSpec, Vote

PROMPT = """You are one independent analyst on a 100-assignment research panel. Answer only from the evidence given.
Assignment: {q}
Falsification condition: {f}
Rule-based draft: vote={vote} finding={finding}
Evidence (id: claim | source | date):
{evidence}
Return JSON {{"vote": "YES"|"NO"|"UNKNOWN", "confidence": 0-1, "finding": str, "support": [ids], "contra": [ids]}}.
UNKNOWN if the evidence does not answer the question. Never invent ids or facts."""


class LlmExecutor:
    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key, self.model, self.base_url = api_key, model, base_url
        self.client = httpx.Client(timeout=60)

    def evaluate(self, spec: AssignmentSpec, view: SliceView, draft: Outcome) -> tuple[Outcome, str]:
        evs = [view.evidence(i) for i in dict.fromkeys(draft.support + draft.contra) if i]
        evs = [e for e in evs if e]
        if not evs:
            return draft, "rule-based"
        text = "\n".join(f"{e.id}: {e.claim[:300]} | {e.source_url} | {e.published_date}" for e in evs)
        msg = PROMPT.format(q=spec.question, f=spec.falsification, vote=draft.vote.value, finding=draft.finding, evidence=text)
        r = self.client.post(f"{self.base_url}/chat/completions", headers={"Authorization": f"Bearer {self.api_key}"},
                             json={"model": self.model, "messages": [{"role": "user", "content": msg}],
                                   "response_format": {"type": "json_object"}, "temperature": 0})
        r.raise_for_status()
        out = json.loads(r.json()["choices"][0]["message"]["content"])
        allowed = {e.id for e in evs}
        support = [i for i in out.get("support", []) if i in allowed]
        vote = Vote(out.get("vote", "UNKNOWN"))
        if vote == Vote.YES and not support:
            return draft, "rule-based (llm YES rejected: no valid evidence)"
        return Outcome(vote, float(out.get("confidence", 0.5)), str(out.get("finding", ""))[:500], support,
                       [i for i in out.get("contra", []) if i in allowed]), f"llm:{self.model}"
