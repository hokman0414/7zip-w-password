# 11 — Feedback Loops and Product Decision

## Phase 9 feedback loop log

Each iteration records the objection, its type, the falsifiable test, the evidence collected, and what changed. The limit was five iterations per candidate; no candidate used more than three.

| # | Candidate | Highest-impact objection | Type | Falsifiable test | Evidence collected | Result | What changed |
|---|---|---|---|---|---|---|---|
| 1 | Original (A + B for AI providers) | "Providers already do this or would build it; no buyer" | **Fundamental business flaw** (suspected) | Find any public signal of providers buying or lacking artifact→session capability | E02–E10, E17 | Providers attribute from the on-platform side, share indicators (E08), and already build generation-time matching (E10). No buyer signal. | H1 rated least likely (doc 04). Scope narrowed to "provider-internal SDK" (H5). Re-vote: overall median 2. **Original rejected as a standalone company.** |
| 2 | B (binary→source engine) | "Source features do not survive compilation" | Evidence gap → technical test | Hybrid R@10 ≥ 0.90 on stripped -O3 **and** FER ≤ 1% on out-of-index, at 10k records | Built the slice and benchmark (E30) | **Passed** for naive builds (R@10 1.000; FER 0/400). **Failed** under string obfuscation plus constant mutation (R@10 0.768; escalation recall 0.20). | Hypothesis revised: "works when the author is not hiding". New question: which buyer's adversary does not hide? |
| 3 | New candidate F (IP code reuse) | "Is there a buyer whose adversary renames but does not obfuscate?" | Evidence gap | Find documented cases where proprietary code was found in a third party's product and how it was concealed; find spend signals | E21–E26 | *Hytera*: copied into firmware, functions renamed (E22). Record trade-secret volume and damages (E23). Source-repo leak monitoring commoditized (E26), but compiled-artifact coverage not found (I07). | Added H8 to the ACH, A14–A19 to the KAC, and P9–P13 to the premortem. Round 2 persona vote: F is the best candidate (median 3; 2/12 at ≥ 4). |
| 4 | F | ML persona: "Synthetic corpus overstates distinctiveness" | Evidence gap → technical test | Rerun with 80% boilerplate strings/constants. Continue if precision holds and IP-transplant R@10 ≥ 0.6. | Boilerplate-heavy run (E30) | Precision 1.0 and FER 0/400 hold. IP-transplant R@10 = 0.66; escalation recall 0.135. | F's claim narrowed to **safe triage leads**, not comprehensive detection. X1 (real-code benchmark) became the gating experiment. |
| 5 | C / E (supply-chain / hybrid malware intel) | "Crowded, and the founder's differentiating assets are unverified" | Evidence gap (assets) + competitive flaw | Locate and inspect the classifier and datasets | Repo inspection (E01); market scan (E17–E19) | Assets absent. Incumbents hold 500k+ labeled packages and large corpora. | C/E marked **blocked** pending asset validation (doc 08 protocols). |
| 6 | D (coding-agent observability) | "Crowded and well funded, no founder edge" | Competitive flaw | Market scan | E27 | Five or more funded entrants; no RE/malware advantage applies. | D **rejected**. |
| 7 | F (Cycle 3, literature) | "The method is prior art and fails on real binaries" | Evidence gap + competitive flaw | Does peer-reviewed real-world evaluation show binary→source matching with recall ≥ 0.8 and precision ≥ 0.9? | E32–E37, E50 (doc 14) | **Falsified for similarity scoring alone** (recall 20–60%; B2SFinder 19.9% / 47.9%). **Supported for retrieve-then-verify** (93.7% / 97.6%; local model 91.0% / 91.9%). EU decompilation is interoperability-only. | Architecture adds a local verification stage. X1 is redesigned on the FSE 2026 public benchmark with published baselines. **F moves from PILOT FIRST to RESEARCH FIRST.** Claim narrowed to an evidence workflow. |
| 8 | G (training-data provenance audit) | "Can an owner prove a model trained on its code?" | Evidence gap | Is there a published method with an evidence-grade false-positive rate on unmarked code? | E48 | Membership inference FPR 0.10; watermarking must be applied before training | G **not pursued**. Signpost: an MI method with FPR ≤ 1%. |

## Decision matrix

Scores are 1–5 and cite evidence. **UNKNOWN** marks criteria where the evidence is insufficient to score; those criteria are excluded from the weighted sum, the sum is renormalized over the known weight, and the full 1→5 range is shown.

| Criterion (weight) | A Provider SDK | B Binary→source platform | C Supply-chain provenance intel | D Coding-agent observability | E Hybrid malware intel + provenance | F IP code-reuse investigation |
|---|---|---|---|---|---|---|
| Unmet need (20%) | 2 (E02 vs E08, E10) | 2 (same) | 3 (E17 market real; provenance part weak) | 3 (E27 funding) | 2 (E19, E20 served) | 3 (E22, E23; indirect) |
| Technical feasibility (15%) | 4 (E30 cost) | 3 (E30a vs E30b) | 4 (E28, mature tools) | 4 | 3 | 3 (E30d default 1.0 vs boilerplate 0.66) |
| Differentiation (15%) | 1 (E10) | 2 (E29, E11) | 1 (E17, E18) | 1 (E27) | 2 (E20) | 3 (I07; low confidence) |
| Founder advantage (10%) | 2 | 4 (RE) | 2 (E01 assets absent) | 1 | 3 | 4 (RE + forensics fit; E21, E22) |
| Customer accessibility (15%) | 1 (≈ 6–15 buyers, E08) | 1 | 3 | 3 | 2 | 2 (legal buyers outside founder network; A24) |
| Willingness to pay (15%) | 1 (E10, PIR-5) | 1 | 3 (E17) | 3 (E27) | 2 | **UNKNOWN** (damages ≠ WTP) |
| Regulatory/privacy (10%) | 3 (provider-hosted only) | 2 | 4 (public data) | 3 | 3 | 3 (owner-held key; A16 open) |
| **Weighted score** | **1.95** | **2.05** | **2.85** | **2.65** | **2.35** | **2.94** on known 85% (range **2.65–3.25**) |
| **F after Cycle 3** (doc 14) | | | | | | Tech 3 (feasible *path* via E36, not shown by us on real data). **Differentiation 3→2** (E32, E33, E36). **Regulatory 3→2** (E50 EU Art. 6). → **2.65** on known 85% (range **2.40–3.00**). |

Reading the matrix:

- No candidate scores ≥ 3.5, so none is a clear BUILD.
- **C and F are statistically indistinguishable on this matrix.**
  - C's score rests on a *proven* market, but it has differentiation 1 against funded incumbents, and its distinctive assets are unverified.
  - F's score rests on *unknown* willingness to pay, but it has the highest differentiation and founder fit.
- **Tie-break rule used:** prefer the candidate whose main uncertainty can be resolved cheaply and quickly. F's uncertainty (WTP, A16) is resolved by about 12 interviews and one counsel opinion. C's uncertainty (out-competing Socket, Checkmarx, and JFrog) is not resolvable by research.
- **After Cycle 3, F's known-criteria score (2.65) is slightly *below* C's (2.85).** The ranges still overlap, and the difference is within scoring noise. The persona medians still favour F (3 vs 2). This is recorded as a genuine weakening of F, not explained away.
  - F stays the evidence-collection target because its open questions are cheap to answer (literature-benchmarked X1, X2, X3).
  - C remains blocked by absent assets (E01).
  - **If F fails X1 or X2, the default is STOP, not C**, unless the founder's assets pass validation.

## Decision

### **PIVOT**

The original concept, an AI-provider binary-to-generation-session attribution platform, is **not** a viable standalone company on current evidence:

- **No buyer:** providers attribute from the on-platform side, share indicators among themselves, and build this pattern in-house.
- **The most important adversaries evade it:** string encryption and constant changes collapse recall.
- **Privacy custody:** session-derived data cannot leave providers.

Release the provider-side SDK pattern (Architecture A) as reference code if useful for relationships; do not build a company on it.

**Pivot target: Candidate F, IP code-reuse investigation.** This is detection of proprietary code compiled into third-party binaries, firmware, apps, and packages, using owner-custodied keyed fingerprints and evidence-grade reporting. F's status is **RESEARCH FIRST** (downgraded from PILOT FIRST in Cycle 3; see doc 14 §8):

- Technical potential was measured only on synthetic data. Peer-reviewed real-world evaluations show similarity scoring alone reaches 20–60% recall (E35, E36). A verification stage is needed and is not yet built or measured by us.
- Buyer demand, willingness to pay, and lawful-acquisition questions are **unvalidated**.
- F did **not** pass the consensus gates (2/12 overall ≥ 4 in Round 2, 1/12 in Round 3; critical legal question A16 open and more severe for the EU). It may not receive build investment beyond the existing slice until the doc 13 gates pass.

Other candidates:

| Candidate | Status |
|---|---|
| C / E | **Blocked**, pending founder asset validation. Revisit only if the classifier and datasets pass the doc 08 protocols *and* reveal data no incumbent has. |
| D | **Rejected.** |
| A / B for AI providers | **Rejected as a company.** B's engine is reused inside F. |
| G Training-data provenance audit | **Not pursued.** Membership-inference false-positive rate is too high for evidence (E48). |
