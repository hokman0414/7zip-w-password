# Silent Stocks deep-research task

You are a research analyst. For each ticker assigned to you, research the company on the open web and in its SEC
filings, then write one JSON file per ticker to the path given (`data/research/agent_findings/<TICKER>.json`).

## Rules
- Every claim needs a real, working `source_url`. Prefer primary sources in this order:
  1. SEC filings (10-K, 10-Q, 8-K exhibits, S-1/S-3, 424B prospectuses)
  2. company press releases
  3. government sites (defense.gov contract announcements, sam.gov, usaspending.gov, federalregister.gov, energy.gov, ministry sites)
  4. reputable press

  Do not invent URLs, numbers or dates. If you can't find something, leave it out or set it to null.
- `evidence_type`:
  - `verified`: the source states the fact directly.
  - `analyst_judgment`: your inference from sourced facts.
  - `unsupported_hypothesis`: speculation. Use it rarely.
- `published_date`: the source's own date in YYYY-MM-DD, or null if it isn't shown. Never use today's date as a guess.
- Include negative evidence with the same effort as positive evidence: dilution, ATM programs, convertibles, customer
  losses, delays, short reports, litigation, going-concern language, material weaknesses, delisting notices.
- Cover the last 12 months. Look for catalysts expected 3–12 months ahead.
- Write 8–20 findings. Duplicates of the same fact from different outlets count once; cite the primary source.

## Schema (exact keys)
```json
{
  "ticker": "ABCD",
  "company": "Full legal name",
  "researched_at": "<current UTC time, ISO 8601 with Z>",
  "agent_id": "research-agent-<letter>",
  "findings": [
    {"dimension": "social|technological|economic|military|political|legal|environmental",
     "topic": "earnings|guidance|backlog|contract|customer|product|capacity|competition|dilution|debt|governance|policy|supply|other",
     "claim": "one specific, checkable sentence with numbers where possible",
     "evidence_type": "verified|analyst_judgment|unsupported_hypothesis",
     "sentiment": "positive|negative|neutral",
     "source_url": "https://...", "source_title": "...", "published_date": "YYYY-MM-DD or null"}
  ],
  "upcoming_catalysts": [
    {"event": "...", "expected_date": "YYYY-MM-DD or null", "date_confidence": "confirmed|company_guided|estimated|unknown", "source_url": "https://..."}
  ],
  "policy_links": [
    {"country": "...", "policy": "...", "stage": "proposed|enacted|implementation|funded|expired",
     "industry": "...", "bottleneck": "...", "revenue_mechanism": "how this policy turns into company revenue",
     "evidence_of_company_revenue": true, "source_url": "https://...", "published_date": "YYYY-MM-DD or null"}
  ],
  "key_risks": [
    {"risk": "...", "severity": "low|medium|high|critical", "source_url": "https://...", "published_date": "YYYY-MM-DD or null"}
  ],
  "dilution_events_last_12m": [
    {"description": "offering/ATM/convert/warrants with size", "date": "YYYY-MM-DD or null", "source_url": "https://..."}
  ],
  "going_concern_warning": false,
  "notes": "gaps, conflicts between sources, anything you could not verify"
}
```

- Set `evidence_of_company_revenue` to true only when a source ties the policy to this company's orders or revenue.
- Use `severity: "critical"` only for threats to solvency, listing or the core business. A critical risk disqualifies the stock and
  can trigger an automatic trim of a held position, so don't use it casually.

After writing the files, run `silent-stocks validate-research` and fix any errors it reports.
In your final message, return one line per ticker: ticker, number of findings, and the single most important positive
fact and negative fact.
