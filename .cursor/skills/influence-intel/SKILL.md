---
name: influence-intel
description: Institution-level influence brief for a named religious or civic organization. Builds a public-record profile (LDA lobbying, Form 990, FEC committees, federal awards, congress.gov, GDELT), runs research subagents, then applies STEMPLE, influence-pathway checks, structured analytic techniques and a next-sponsorship outlook. Use when asked to assess how an organization sustains influence, what it is likely to sponsor next, or to refresh an existing influence brief.
---

# Influence Intel brief

## Hard rules

- Institution level only. Never profile private individuals, members or individual donors, and never infer anyone's
  religion or politics. Leaders appear only in their public roles.
- Every claim cites a source. UNKNOWN stays UNKNOWN; do not fill gaps with guesses.
- Outlook scores are ranking indexes, not probabilities. LDA filings do not reveal support vs opposition.
- Describe lawful, transparent activity. Decline requests to design deception, coercion, covert or foreign influence
  operations, or targeting of any group.

## Steps

1. Setup: `test -d .venv || (python3 -m venv .venv && .venv/bin/pip install -e '.[dev]')`.
2. Profile. If `profiles/<slug>.json` does not exist:
   - `.venv/bin/influence-intel find "<name>"` (repeat for major affiliates: charities, health systems, schools,
     advocacy arms, PACs).
   - Keep only matches you can confirm are the organization (check state, NTEE code, website). Write the profile using
     `profiles/example_catholic_charities_usa.json` as the template. Set `is_church_exempt_from_lda: true` when the core
     body is a church or convention of churches.
3. Research: launch up to 3 subagents in parallel with `influence_intel/prompts/research_agent.md` (fill `{name}`,
   `{slug}`, `{as_of}`). Split the work across them (for example: membership, trust and services; policy, initiatives and
   policy windows; media, digital and international). Merge their output into one `data/influence/research/<slug>.json`
   and run `.venv/bin/influence-intel validate-research data/influence/research/<slug>.json` until it passes.
4. Analyze: `.venv/bin/influence-intel analyze profiles/<slug>.json`. If GDELT or congress.gov rate-limits, wait a
   minute and run again; responses are cached. The brief scores every pathway, every subgroup, and 1,000 hypotheses
   of the form "this subgroup supports this target through this pathway". Each hypothesis carries ACH diagnostics, its
   assumptions, a red-team note and a sensitivity check. The support index is a ranking, not a probability.
5. Review the brief in `reports/influence/<slug>/<date>.md`:
   - Spot-check five outlook items and three pathway checks against their evidence ids in the JSON.
   - Confirm the news query is not matching namesakes.
6. Commit `profiles/`, `data/influence/research/` and `reports/influence/` with message `influence: <slug> <date>`, push,
   and reply with the posture assessment, top 5 outlook items with their basis, the most exposed pathways, and the data
   gaps.

## Optional keys (Cursor Dashboard -> Cloud Agents -> Secrets)

`FEC_API_KEY` and `CONGRESS_API_KEY` (free api.data.gov keys) lift the DEMO_KEY rate limits.
