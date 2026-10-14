#!/usr/bin/env bash
# Small smoke run: a few conferences + limited transcripts
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
cd "$(dirname "$0")/.."
cyber-talks run \
  --conference defcon \
  --conference blackhat-usa \
  --conference bsides-sf \
  --years 2 \
  --enrich-limit 40 \
  --limit 20 \
  --min-score 3.0
cyber-talks stats
