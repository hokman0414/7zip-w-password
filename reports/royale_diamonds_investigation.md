# Royale Diamonds Investigation Report

**Case ID:** `royale_diamonds`  
**As of (UTC):** 2026-10-20T02:39:43.509803+00:00  
**Method:** Evidence-first OSINT; competing hypotheses; no fabricated sources.

## 1. Executive intelligence assessment

| Topic | Status | Assessment |
|---|---|---|
| Seller public identity | CORROBORATED | TikTok `@royalediamondslive` linked by Mashable and live profile |
| Legal business entity | UNKNOWN | No verified SOS linkage yet |
| IGI certificate LG839637366 | CONFIRMED | Exists; lab-grown marquise 3.03ct F / VS1 / CVD |
| Spec match to listing | MOSTLY MATCH / Polish CONTRADICTED | IGI polish = Very Good; listing said Excellent |
| Economic plausibility of $350 | CORROBORATED as plausible auction price | Below observed retail-ask median; not proof of fraud |
| Fulfillment | UNKNOWN | Tracking `9200190390470924693050` — NO_PUBLIC_SCAN_DATA — aggregator reports no information; USPS authoritative portal blocked from this environment. Do not infer transit progress. |
| Leading hypotheses | Qualitative | H2, H1 (subjective posteriors, not base rates) |

### Recommended actions
- Manually open USPS tracking for 9200190390470924693050 and archive screenshot (portal blocked here).
- On receipt: verify girdle inscription 'IGI LG839637366' and compare measurements to IGI fields.
- Note polish grade mismatch (Excellent advertised vs Very Good on IGI) for dispute leverage if needed.
- Provide TikTok Shop order ID, seller legal name, and promised ship-by date to tighten corporate OSINT.
- If no USPS acceptance scan by ship-by + 3 business days, open TikTok Shop dispute.


## 2. Evidence ledger

Append-only ledger files:
- `evidence/normalized/evidence_ledger.json`
- `evidence/normalized/evidence_ledger.csv`

Records currently persisted: **18**

Every factual claim below cites evidence IDs or source URLs actually accessed in this run.

## 3. Diamond certificate verification

**Source (CONFIRMED):** `https://lookup.igi.org/igi_new.php?r=LG839637366`  
**Verify page:** `https://lookup.igi.org/index.php/reports/verify_your_report?r=LG839637366`

| Field | IGI (CONFIRMED) | Advertised | Result |
|---|---|---|---|
| report_number | LG839637366 | LG839637366 | MATCH |
| shape | MARQUISE BRILLIANT | MARQUISE BRILLIANT | MATCH |
| carat | 3.03 Carats | 3.03 Carats | MATCH |
| color | F | F | MATCH |
| clarity | VS 1 | VS 1 | MATCH |
| measurements | 14.39 x 7.67 x 4.78 mm | 14.39 x 7.67 x 4.78 mm | MATCH |
| table | 61% | 61% | MATCH |
| depth | 62.3% | 62.3% | MATCH |
| fluorescence | NONE | NONE | MATCH |
| polish | VERY GOOD | Excellent | MISMATCH |
| growth_method | This Laboratory Grown Diamond was created by Chemical Vapor Deposition (CVD) growth process Type IIa | CVD | MATCH |

**Additional IGI fields:**  
Report date: September 19, 2026  
Symmetry: EXCELLENT  
Girdle: MEDIUM TO SLIGHTLY THICK (FACETED)  
Culet: POINTED  
Comments: This Laboratory Grown Diamond was created by Chemical Vapor Deposition (CVD) growth process Type IIa  
Inscription(s): IGI LG839637366

**Manual checkpoint:** If PDF download is Cloudflare-blocked, open the verify page in a normal browser and save the PDF/screenshot into `evidence/raw/`.

## 4. Retail / wholesale pricing

Observed **retail asking** prices for similar 2.8–3.2ct F/VS1 IGI marquises (n=10):

- Median ask: **$1236.58**
- Range: $624.0 – $1856.9
- IQR: [720.75, 1496.85]
- Median $/ct: $417.03
- Auction discount vs median ask: 0.717
- Caveat: These are asking prices, not verified transaction prices.

UNVERIFIED leads: Ritani ~$945 (wholesale estimate ~$325.97); Brilliance ~$2,020 — **not independently reproduced**.

Assessment: $350 (~$116/ct) sits below the observed retail-ask cluster for similar F/VS1 marquises, but community heuristics (~$100/ct) and media bands (~$100–200/ct) make auction pricing plausible. Without a verified wholesale feed for LG839637366, 'below cost' cannot be confirmed.

## 5. Seller identity graph

Confirmed / candidate public nodes:
- `tiktok:royalediamondslive` — confidence HIGH: Mashable link + live public profile title/bio
- `instagram:RoyaleDiamondsLive` — confidence MEDIUM: Self-asserted in TikTok bio; Instagram web view required login (blocked)
- `telegram:royalediamondslive` — confidence LOW: Public t.me page reachable; ownership not confirmed

Name collisions explicitly excluded from attribution:
- Royale Diamonds (Pune, India jewelry store) (UNVERIFIED)
- Royal Diamond USA LLC (Bellaire, TX consumer products) (IRRELEVANT_NAME_COLLISION)

Telegram: UNKNOWN — no confirmed official Telegram channel identified

## 6. Fraud hypothesis matrix (ACH)

- **H1**: Legitimate sale of the advertised diamond — subjective posterior 0.227; inconsistency count 1
- **H2**: Legitimate sale with exaggerated retail-value claims — subjective posterior 0.487; inconsistency count 0
- **H3**: Genuine diamond shipped but different from advertised certificate — subjective posterior 0.097; inconsistency count 0
- **H4**: Counterfeit, simulant, or materially misrepresented stone shipped — subjective posterior 0.032; inconsistency count 2
- **H5**: Seller fails to fulfill the order — subjective posterior 0.107; inconsistency count 1
- **H6**: Fraudulent impersonation of a legitimate diamond seller — subjective posterior 0.049; inconsistency count 2

Diagnostic highlights:
- E1 (IGI match) supports certificate reality; does not prove the shipped stone will match.
- E2 (polish mismatch) is disconfirming for perfect representation (hurts H1 relative to H2).
- E6 (no tracking scans yet) is weakly consistent with H5 only because purchase is recent.

## 7. Monitoring dashboard

| Milestone | Value |
|---|---|
| Purchase date | 2026-10-19 |
| Order status | PAID_VIA_TIKTOK_SHOP_USER_REPORTED |
| Ship-by (seller promised) | UNKNOWN — need user input |
| Tracking | 9200190390470924693050 |
| Carrier | USPS |
| Shipment status | NO_PUBLIC_SCAN_DATA — aggregator reports no information; USPS authoritative portal blocked from this environment. Do not infer transit progress. |
| Delivery | NOT_DELIVERED_UNVERIFIED |

### Indicators to watch
- **seller_impersonation**: Sudden username/branding change; Mismatched shop legal name vs livestream branding
- **order_cancellation**: TikTok order cancelled by seller; Refund without shipment
- **shipping_nonfulfillment**: No scan beyond label-created after promised ship-by + buffer; Tracking never issued
- **fake_tracking**: Tracking number not recognized by USPS; Tracking for unrelated origin/destination
- **certificate_mismatch**: Received report number ≠ LG839637366; Girdle inscription missing/mismatch
- **diamond_substitution**: Measurements off beyond tolerance; Different clarity/color under gemologist check
- **unusual_refund_behavior**: Pressure to accept store credit only; Refusal to use TikTok Shop dispute channel


## 8. Evidence gaps / blocked sources

- USPS authoritative tracking portal: Access Denied / bot wall from this environment.
- IGI PDF endpoint (`api.igi.org/viewpdf.php`): Cloudflare challenged.
- Ritani / several marketplaces: Cloudflare or 403.
- Reddit JSON API: blocked.
- OpenCorporates search: reCAPTCHA wall.
- Instagram web profile: login wall (bio claim remains self-asserted).
- Exact TikTok Shop seller legal business name: missing (need order receipt).

## Claim status legend

CONFIRMED · CORROBORATED · UNVERIFIED · CONTRADICTED · UNKNOWN · BLOCKED

---
*Generated by the Royale Diamonds OSINT pipeline. Do not treat subjective Bayesian posteriors as calibrated probabilities.*
