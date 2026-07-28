# Clinical Calculator Implementation Readiness

Updated baseline: 2026-07-28

## Runtime inventory

The built-in registry contains executable calculators only.

| Level | Logical entries | Meaning |
| --- | ---: | --- |
| complete | 593 | Executable from original declared inputs |
| partial | 50 | Executable intermediate step using pre-scored or upstream values |
| total | 643 | All entries have local calculation logic |

The CSV contains 727 rows because 84 retired duplicate IDs remain as compatibility aliases. They resolve to canonical executable entries and are not counted as separate calculators.

The loader rejects any built-in inventory row that has no linked implementation. Incomplete proposals, guideline-only knowledge, and content without redistribution rights are not stored in the runtime inventory.

## Medical review gate

Executability and clinical release remain separate. A calculator is not release-ready unless:

1. The implementation level is `complete`.
2. The exact source version or publication year is recorded.
3. The source URL identifies the calculator, guideline, or original publication rather than a library landing page.
4. Interpretation thresholds are stored locally and do not defer to an unspecified external source.
5. Independent source-derived validation cases cover ordinary, threshold, unit-conversion, and invalid inputs.
6. A qualified reviewer has approved the calculator for the intended setting.

Currently 19 entries pass the automated metadata portion of this gate. The explicit clinician-approved release allowlist remains empty.

## Result status contract

| Status | Meaning |
| --- | --- |
| implemented | Calculation completed |
| partial | An executable intermediate result was calculated |
| missing_inputs | One or more declared inputs were omitted |
| invalid_inputs | Values failed type, finite-number, range, choice, or arithmetic validation |

Requests for calculators outside the registry return no match. The Agent must not reconstruct missing or protected rules from memory.
