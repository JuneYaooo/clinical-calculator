---
name: clinical-calculator
description: Use for searching, selecting, calculating, checking, or explaining clinical formulas, medical calculators, risk and staging scores, renal estimates, lab-derived indices, unit conversions, dose arithmetic, or interpretation thresholds; also use to audit calculator availability or turn a supplied JSON, CSV, Markdown, PDF, DOCX, or written specification into a draft, validated, and installed user-defined scalar/multi-output formula, lookup table, or decision-tree calculator. Supports Chinese and English calculator names and explicitly separates executable, research-candidate, guidance, controlled, reviewed, and released states.
---

# Clinical Calculator

Use this repository as a calculation and evidence-routing Skill, not as a product interface. The inventory is broad, but not every indexed entry is executable or cleared for clinical release.

## Core workflow

1. Search executable calculators before choosing a formula:

   ```bash
   python3 scripts/clinical_calculator.py search "<中文名、英文名、专科或场景>"
   ```

   Default search excludes non-executable catalog entries. Use `--all` for the complete
   catalog or `--layer source_candidate|guidance_knowledge|controlled_content` when auditing.

2. Resolve duplicate names by ID. Never silently choose among multiple versions or variants.
3. Inspect the exact inputs, units, bounds, source, version, and implementation state:

   ```bash
   python3 scripts/clinical_calculator.py info CALC-0039
   ```

4. Ask for any missing or ambiguous input. Do not assume sex, pregnancy, pediatric/adult population, race term, body size, timing, acute stability, or unit.
5. Run by exact ID with JSON-compatible values:

   ```bash
   python3 scripts/clinical_calculator.py run CALC-0039 \
     --input weight_kg=70 --input height_cm=175
   ```

6. Report calculator/version, inputs and units, formula or rule, result and rounding, interpretation, source, and important limits. Keep arithmetic reproducible.

Read [references/calculator-cli.md](references/calculator-cli.md) for all commands and result states.
Read [references/search-and-routing.md](references/search-and-routing.md) for query normalization,
synonym maintenance, match explanations, and the required response to `no_match`.

## Availability and safety

- `complete` means locally executable from its declared contract, not clinically approved.
- `partial` returns an intermediate result or needs upstream/pre-scored values.
- `metadata_only` is searchable but must return `needs_formula_implementation`.
- `licensed_rule` is intentionally unavailable because exact content is rights- or subscription-governed.
- `released` is controlled separately by an explicit clinician-approved allowlist. It is currently empty.
- Catalog layers are separate from execution state: `executable`, `source_candidate`,
  `guidance_knowledge`, and `controlled_content`. Do not present the latter three as runnable.
- Resolve merged duplicate IDs through `clinical_calculator_aliases.csv`. Treat the canonical ID as
  the calculator record; keep old IDs working for backward compatibility and do not count aliases
  as separate calculators.
- Treat the MIT license as covering repository code, not as permission to reproduce third-party
  questionnaire text, proprietary tables, staging content, or other controlled clinical material.
- Never reconstruct missing coefficients, point tables, nomograms, licensed questionnaire items, or versions from memory.
- Read [references/input-contracts.md](references/input-contracts.md) before adding or changing an executable calculator's declared inputs.
- For medication dosing, separate calculation from prescribing and require clinician/pharmacist review.
- For emergencies or high-stakes decisions, do not let a calculator replace urgent professional assessment.

When an entry cannot run, explain its state and required source material. Offer a runnable alternative only if it answers the same clinical question and clearly identify any population or version difference.

Rank the current evidence-retrieval candidates before source work:

```bash
python3 scripts/clinical_calculator.py backlog --limit 110
python3 scripts/clinical_calculator.py backlog --blocker formula_missing
```

This queue is generated from `reports/calculator_implementation_status.csv`; do not infer missing
rules from the queue metadata itself.

## Add a custom calculator

Scaffold a safe declarative formula, lookup table, or decision tree:

```bash
python3 scripts/clinical_calculator.py scaffold \
  --output /tmp/my-calculator.json \
  --id CUSTOM-MY-CALC \
  --name-cn "我的计算器" \
  --name-en "My Calculator"
```

Add `--kind multi-formula`, `--kind lookup`, `--kind multi-lookup`, or
`--kind decision-tree` for those templates. `multi-lookup` demonstrates exact + range dimensions
and named multiple outputs. Schema v2 manifests must include at least one source-derived test case
and may record source effective/retrieval dates.

Then replace the example formula and placeholder source, validate it, test known cases, and install it:

```bash
python3 scripts/clinical_calculator.py validate-custom /tmp/my-calculator.json
python3 scripts/clinical_calculator.py install-custom /tmp/my-calculator.json
python3 scripts/clinical_calculator.py run CUSTOM-MY-CALC --input example_value=1
```

### Create from a supplied file

Read `references/custom-calculators.md`, then:

1. Confirm the material defines a calculator rather than containing patient-specific values. Never
   persist patient identifiers or case data in a calculator manifest.
2. Validate an existing JSON manifest directly. For CSV, Markdown, PDF, DOCX, or prose, extract
   only explicit inputs, units, bounds, formula/table/tree rules, interpretations, source/version,
   and source-derived known answers.
3. Never infer missing coefficients, thresholds, table cells, units, or versions. Save incomplete
   work under `custom_calculators/drafts/<custom-id>.json`; nested drafts are not executable.
4. Generate schema v2 and run `validate-custom`. If evidence or validation is incomplete, leave the
   file as a draft and report exactly what is missing.
5. Show the proposed ID, inputs, calculation rule, source, and tests. Install only after confirmation:

   ```bash
   python3 scripts/clinical_calculator.py install-custom \
     custom_calculators/drafts/<custom-id>.json
   ```

6. Verify the installed calculator with `info` and one source-derived `run` case. Installed
   manifests are saved directly under `custom_calculators/` and discovered on later runs.

Custom manifests are sandboxed to allowlisted expression syntax. Exact, range, and multidimensional
lookup tables never interpolate implicitly; decision-tree rules use first-match order. Manifests are discovered
from `custom_calculators/`, additional `--custom-dir` paths, or
`CLINICAL_CALCULATOR_CUSTOM_DIRS`. They are runnable but never automatically clinically released
or considered independently reviewed.

Read [references/custom-calculators.md](references/custom-calculators.md) before authoring or
reviewing an extension. Use a source-backed Python implementation with tests for interpolated
tables, dates, sequences, licensed content, or other unsupported logic.

## Response pattern

Use concise prose or this structure when the calculation is non-trivial:

```text
Calculator / version:
Inputs / units:
Formula or rule:
Result:
Interpretation:
Source:
Limits / review state:
```
