# Royale Diamonds OSINT Investigation

Evidence-first investigation workspace and reusable Python pipeline for a TikTok Shop livestream diamond auction case.

## Quick start

```bash
python3 -m pip install -r requirements.txt
python3 main.py investigate --case royale_diamonds
python3 main.py verify-diamond --igi LG839637366
python3 main.py research-seller --name "Royale Diamonds"
python3 main.py monitor --case royale_diamonds --tracking 9200190390470924693050
python3 main.py report --case royale_diamonds
python3 -m pytest -q
```

## Key outputs

- `reports/royale_diamonds_investigation.md`
- `reports/royale_diamonds_investigation.json`
- `evidence/normalized/evidence_ledger.json` / `.csv`
- `research/diamonds/igi_LG839637366_verified.json`

## Ethics / constraints

- Public sources only
- Respect robots.txt, rate limits, and platform terms
- No CAPTCHA bypass, no private-account access, no private-person doxxing
- Missing/blocked sources are marked explicitly — never fabricated
