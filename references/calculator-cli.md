# Calculator CLI

Run commands from the Skill root. Output is JSON so an agent can inspect it without scraping prose.

## Discover and inspect

```bash
python3 scripts/clinical_calculator.py summary
python3 scripts/clinical_calculator.py search "Glasgow"
python3 scripts/clinical_calculator.py search "肾功能" --limit 10
python3 scripts/clinical_calculator.py search "CRIB-II" --layer source_candidate
python3 scripts/clinical_calculator.py backlog --limit 110
python3 scripts/clinical_calculator.py search "筛查" --all
python3 scripts/clinical_calculator.py info CALC-0039
```

Search defaults to the `executable` layer. `--all` searches the full catalog; `--layer` selects
`executable`, `source_candidate`, `guidance_knowledge`, or `controlled_content`. The legacy
`--runnable` flag is equivalent to the default. Search covers Chinese and English names, category,
subspecialty, scenario, purpose, and source. If a display name has multiple rows, `info` and `run`
reject ambiguity and list the valid IDs.

Each result reports `catalog_layer`, `implementation_level`, and `pending_blocker_type`. A retained
guideline, research candidate, staging system, or licensed scale must not be described as executable.

`info` returns the machine-readable input contract. Check every input's `name`, `value_type`, `unit`, range, choices, and description before running it.

## Run

```bash
python3 scripts/clinical_calculator.py run CALC-0039 \
  --input weight_kg=70 \
  --input height_cm=175
```

Input values are parsed as JSON when possible. Examples: `42`, `3.5`, `true`, `false`, `"female"`, `[1,2,3]`. Unquoted plain text is preserved as a string. Unknown or repeated input keys are rejected.

Exit code is zero for a completed or partial calculation and 2 for invalid, missing, unresolved, ambiguous, or unavailable calculations.

Result states:

- `implemented`: local calculation completed.
- `partial`: an intermediate calculation completed but another step or externally supplied component is still required.
- `missing_inputs`: one or more declared inputs were not supplied.
- `invalid_inputs`: a type, finite-number, range, choice, or arithmetic check failed.
- `needs_formula_implementation`: the inventory entry has no audited local implementation.

The CLI includes formula text and source URL in run output. Confirm that the formula/version applies to the stated population; executable does not mean clinically released.

## Validate

```bash
python3 scripts/clinical_calculator.py validate
python3 scripts/clinical_calculator.py validate-custom path/to/calculator.json
```

`validate` loads the entire registry, detects custom ID conflicts, and checks required metadata. It does not substitute for independent formula verification or clinical review.

`backlog` reads `reports/calculator_implementation_status.csv` and ranks the current source candidates
by evidence work needed. Use `--blocker formula_missing` (or another listed blocker) to focus the
queue. Its source links are starting points; a candidate becomes executable only after complete
rules, version, units, boundaries, rights, and source-derived test cases are verified.

Exact duplicate inventory rows are merged through `clinical_calculator_aliases.csv`. `info` and
`run` accept either the canonical ID or a merged legacy ID; results report the canonical ID.

## Custom discovery

The default directory is `custom_calculators/` in the Skill root. Add one or more temporary locations before the command:

```bash
python3 scripts/clinical_calculator.py \
  --custom-dir /path/to/team-calculators \
  --custom-dir /path/to/local-calculators \
  search "custom"
```

The `CLINICAL_CALCULATOR_CUSTOM_DIRS` environment variable also accepts multiple directories separated by the operating system path separator.
