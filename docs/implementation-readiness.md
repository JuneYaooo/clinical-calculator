# Clinical Calculator Implementation Readiness

Generated baseline: 2026-07-15

## Current Runtime Classification

| Level | Rows | Meaning |
|---|---:|---|
| complete | 667 | Executable from its declared local input contract |
| partial | 55 | Uses pre-scored/upstream values or implements only an intermediate step |
| metadata_only | 325 | Metadata is searchable but no executable implementation is linked |
| licensed_rule | 91 | Blocked by rights or versioned/subscription-governed content |

These levels total 1138 inventory rows. They are intentionally separate from medical review readiness. Source-backed promotions now include CALC-0285, CALC-0479, CALC-0569, CALC-0714, CALC-0162, CALC-0746, CALC-0758, CALC-0067, CALC-0642, CALC-0693, CALC-0387, CALC-0701, CALC-0525, CALC-0765, CALC-0712, and CALC-0711.

## Catalog Layers

| Layer | Rows | Default discovery behavior |
|---|---:|---|
| executable | 722 | Included in default CLI search |
| source_candidate | 126 | Retained for formula/source research; requires explicit layer search |
| guidance_knowledge | 199 | Retained as pathway, drug-rule, or prevention knowledge; not runnable |
| controlled_content | 91 | Retained as rights- or staging-governed metadata; not runnable |

Catalog layer and implementation level are independent concepts. Exact-ID `info` remains available
for every retained row, while default search avoids presenting non-executable knowledge as a
calculator result.

## Medical Review Gate

A calculator is not release-ready unless all of the following are true:

1. Its implementation level is `complete`.
2. The exact source version or publication year is recorded.
3. The source URL identifies the calculator, guideline, or original publication rather than a library landing page.
4. Interpretation thresholds are stored locally and do not defer to an unspecified external source.
5. Independent source-derived validation cases cover ordinary, threshold, unit-conversion, and invalid inputs.

At this baseline, 17 of 1138 rows have a version/year and 16 rows pass the automated portion of this gate. Passing the automated gate is not a substitute for clinician review.

## Result Status Contract

| Status | Meaning |
|---|---|
| implemented | Calculation completed |
| partial | An intermediate result was calculated; another referenced step is required |
| missing_inputs | The implementation exists but required inputs were omitted |
| invalid_inputs | Values failed type, finite-number, range, or formula validation |
| needs_formula_implementation | No executable formula/rule is linked |

## Priority Backlog

Do not infer coefficients or licensed tables from summaries. The next source-backed implementation batch should prioritize:

1. ASCVD, PREVENT, and FRAX after exact coefficients, population limits, caps, and validation cases are captured; the four-variable KFRE is now implemented.
2. Neonatal early-onset sepsis and VBAC models after the current official model/version is selected.
3. Acetaminophen and Hartford nomograms with governed chart data and boundary tests.
4. WHO/CDC/fetal growth calculations with versioned reference tables bundled locally.
5. Antimicrobial renal adjustment as a versioned drug-rule dataset, not a single scalar formula.

ACR pathways, AJCC/NCCN staging, screening schedules, and drug guidance should be implemented as versioned rule tables with effective dates. They should not be reclassified as ordinary formulas merely to raise the implementation count.
