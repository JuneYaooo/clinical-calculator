# Custom Calculator Manifests

Use JSON manifests for deterministic scalar or named multi-output formulas, exact/range lookup
tables, multidimensional exact/range lookup tables, ordered decision trees, point sums, and
threshold interpretation. Schema version 1 formulas remain supported;
prefer schema version 2 for new calculators because it embeds source-derived validation cases.
Start from `assets/custom-calculator.example.json`,
`assets/custom-calculator.multidimensional.example.json`, or the `scaffold` command.

## Required structure

```json
{
  "schema_version": 2,
  "id": "CUSTOM-EXAMPLE-001",
  "category": "通用",
  "scenario": "示例场景",
  "name_cn": "自定义示例",
  "name_en": "Custom Example",
  "purpose": "说明计算目的",
  "inputs": [
    {
      "name": "weight_kg",
      "type": "number",
      "unit": "kg",
      "minimum": 0,
      "exclusive_minimum": true,
      "description": "体重"
    },
    {
      "name": "height_cm",
      "type": "number",
      "unit": "cm",
      "minimum": 0,
      "exclusive_minimum": true,
      "description": "身高"
    }
  ],
  "output": {"unit": "kg/m^2", "round": 2},
  "calculation": {
    "type": "formula",
    "expression": "weight_kg / ((height_cm / 100) ** 2)"
  },
  "interpretation": [
    {"when": "value < 18.5", "text": "低于参考范围"}
  ],
  "default_interpretation": "未匹配分层",
  "test_cases": [
    {
      "name": "source example",
      "inputs": {"weight_kg": 70, "height_cm": 175},
      "expected_value": 22.86,
      "tolerance": 0
    }
  ],
  "source": {
    "type": "publication",
    "name": "具体指南或原始文献",
    "url": "https://example.org/specific-source",
    "version": "2026",
    "effective_date": "2026-01-01",
    "retrieved_at": "2026-07-15",
    "evidence_tier": "custom; requires review"
  }
}
```

Every manifest requires a specific HTTP(S) source URL and a version or year. Optional
`effective_date` and `retrieved_at` values must use `YYYY-MM-DD`. Placeholder sources are
structurally valid for scaffolding, but `install-custom` rejects them until the exact source and
version replace the placeholder markers.

IDs must start with `CUSTOM-` and contain only uppercase letters, digits, and hyphens. IDs must be unique across every discovered custom directory and cannot replace built-in calculators.

## Input types

- `number`: accepts finite numeric values. A unit is required; use `"1"` for a dimensionless value. Optional `minimum`, `maximum`, `exclusive_minimum`, and `exclusive_maximum` set bounds.
- `boolean`: accepts JSON booleans or numeric `0`/`1`, not strings such as `"true"`.
- `choice`: requires at least two unique, non-empty strings and accepts only an exact declared value.

All inputs are required in schema versions 1 and 2. Input names must be valid identifiers and cannot use reserved names such as `value`, `sqrt`, or `min`.

Unknown fields are rejected at every level so spelling mistakes cannot silently disable a bound or rule. `default_interpretation` is required even when the interpretation list is empty.

## Calculation types

Use `calculation.type: formula` with the expression language below.

For multiple named results, replace `output` with at least two `outputs` definitions and use
`calculation.type: formula_set`. Each output has a unique non-reserved identifier, unit, and
rounding rule; `expressions` must contain exactly the same names. Output names cannot duplicate
input names. Example:

```json
{
  "outputs": [
    {"name": "score", "unit": "points", "round": 0},
    {"name": "risk_percent", "unit": "%", "round": 1}
  ],
  "calculation": {
    "type": "formula_set",
    "expressions": {
      "score": "age_years / 10",
      "risk_percent": "age_years * 0.5"
    }
  }
}
```

Use `lookup_table` for one-dimensional source tables. Set `match` to `exact` and give each row a
unique `key`, or set it to `range` and provide `minimum`/`maximum` bounds. Bounds default to an
included minimum and excluded maximum. Set `include_minimum` or `include_maximum` explicitly at
clinical boundaries. Overlapping rows are rejected, missing rows fail at runtime, and interpolation
never occurs implicitly.

Use `multidimensional_lookup` when a complete source table is selected by two or more declared
dimensions. Each dimension declares an input and `exact` or `range` matching. Every row's `keys`
must cover every dimension. A row uses scalar `value` or, for named outputs, a `values` object.
Rows are rejected only when they overlap in every dimension. This supports discrete source tables;
it never performs interpolation or nearest-neighbor matching.

Use `decision_tree` with ordered `rules`, each containing `when`, scalar `value` or named `values`,
and optional `interpretation`. The first matching rule wins. A shape-compatible `default` branch is
required.

Create templates with:

```bash
python3 scripts/clinical_calculator.py scaffold --kind formula ...
python3 scripts/clinical_calculator.py scaffold --kind multi-formula ...
python3 scripts/clinical_calculator.py scaffold --kind lookup ...
python3 scripts/clinical_calculator.py scaffold --kind multi-lookup ...
python3 scripts/clinical_calculator.py scaffold --kind decision-tree ...
```

## Expression language

Allowed constructs:

- Arithmetic: `+`, `-`, `*`, `/`, `%`, and `**`.
- Comparisons: `==`, `!=`, `<`, `<=`, `>`, and `>=`.
- Boolean logic: `and`, `or`, and `not`.
- Conditional expression: `a if condition else b`.
- Functions: `abs`, `min`, `max`, `round`, `sqrt`, `log`, `log10`, and `exp`.
- Numeric, boolean, and string constants.

Attribute access, imports, subscripts, comprehensions, lambdas, arbitrary calls, and keyword arguments are rejected. Expressions have a complexity limit, and constant exponents are limited to -100 through 100. Results must be finite numbers.

Interpretation rules are tested in order. Scalar calculators may reference all inputs plus `value`;
multi-output calculators may reference all inputs plus each named, rounded output. The first true
condition wins; otherwise `default_interpretation` is used.

## Embedded validation cases

Schema version 2 requires at least one `test_cases` entry. Each case supplies every declared input,
an `expected_value` for scalar output or complete `expected_values` object for named outputs,
optional nonnegative `tolerance`, and optional `expected_interpretation`.
Manifest loading executes these cases. A wrong boundary, stale table value, missing input, or changed
interpretation therefore fails `validate-custom` and installation.

## Authoring and review workflow

1. Scaffold the correct calculation type or copy the example.
2. Replace every placeholder and record the exact source/version.
3. Express the formula without inventing missing coefficients or thresholds.
4. Run `validate-custom`.
5. Add source-derived ordinary and boundary examples to `test_cases`; then load through
   `--custom-dir` and separately test invalid and unit-conversion cases.
6. Have a qualified independent reviewer verify population, exclusions, formula, thresholds, units, rounding, and version.
7. Run `install-custom`. Installation makes it discoverable and runnable; it does not add it to the clinical release allowlist.

## When JSON is not enough

Do not force these into the declarative format:

- age/date-dependent lookup rules;
- incomplete tables, growth curves, nomograms, or any table requiring interpolation;
- sequences or variable-length questionnaires;
- versioned staging or drug-rule tables;
- proprietary or licensed question text;
- formulas requiring specialized external libraries.

Add those as source-backed Python implementations under `clinical_calculators/calculators/`, declare their exact input contract, and include source-derived unit, threshold, boundary, and invalid-input tests. Licensed content remains `licensed_rule` until redistribution and implementation rights are clear.
