# Calculator CLI

Run commands from the Skill root. Output is JSON so an agent can inspect it without scraping prose.

## Discover and inspect

```bash
python3 scripts/clinical_calculator.py summary
python3 scripts/clinical_calculator.py search "Glasgow"
python3 scripts/clinical_calculator.py search "肾功能" --limit 10
python3 scripts/clinical_calculator.py info CALC-0039
```

The registry contains executable calculators only. Search covers Chinese and English names,
category, subspecialty, scenario, purpose, and source. If a display name has multiple rows, `info`
and `run` reject ambiguity and list the valid IDs.

Each result reports its `implementation_level`: `complete` for calculations that start from original
inputs, or `partial` for executable intermediate calculations that require pre-scored or upstream values.

`info` returns the machine-readable input contract. Check every input's `name`, `value_type`, `unit`, range, choices, and description before running it.

## Run

```bash
python3 scripts/clinical_calculator.py run CALC-0039 \
  --input weight_kg=70 \
  --input height_cm=175
```

Input values are parsed as JSON when possible. Examples: `42`, `3.5`, `true`, `false`, `"female"`, `[1,2,3]`. Unquoted plain text is preserved as a string. Unknown or repeated input keys are rejected.

Exit code is zero for a completed or partial calculation and 2 for invalid, missing, unresolved, or ambiguous calculations.

Result states:

- `implemented`: local calculation completed.
- `partial`: an intermediate calculation completed but another step or externally supplied component is still required.
- `missing_inputs`: one or more declared inputs were not supplied.
- `invalid_inputs`: a type, finite-number, range, choice, or arithmetic check failed.

The CLI includes formula text and source URL in run output. Confirm that the formula/version applies to the stated population; executable does not mean clinically released.

## Validate

```bash
python3 scripts/clinical_calculator.py validate
python3 scripts/clinical_calculator.py validate-custom path/to/calculator.json
```

`validate` loads the entire registry, detects custom ID conflicts, and checks required metadata. It does not substitute for independent formula verification or clinical review.

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
