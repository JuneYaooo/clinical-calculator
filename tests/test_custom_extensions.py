from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from clinical_calculators import ManifestError, load_custom_manifest, load_registry


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "clinical_calculator.py"


def manifest(calculator_id: str = "CUSTOM-TEST-001") -> dict:
    return {
        "schema_version": 1,
        "id": calculator_id,
        "category": "测试",
        "scenario": "扩展测试",
        "name_cn": "自定义安全公式",
        "name_en": "Custom Safe Formula",
        "purpose": "测试声明式扩展",
        "inputs": [
            {"name": "amount", "type": "number", "unit": "mg", "minimum": 0},
            {"name": "enabled", "type": "boolean"},
            {"name": "mode", "type": "choice", "choices": ["standard", "reduced"]},
        ],
        "output": {"unit": "mg", "round": 2},
        "formula": {
            "expression": "amount * (0.5 if mode == 'reduced' else 1) if enabled else 0"
        },
        "interpretation": [{"when": "value == 0", "text": "未启用"}],
        "default_interpretation": "已计算",
        "source": {
            "type": "publication",
            "name": "Test source",
            "url": "https://example.org/test-source",
            "version": "2026",
            "evidence_tier": "custom; requires review",
        },
    }


def schema_v2(calculator_id: str) -> dict:
    payload = manifest(calculator_id)
    payload["schema_version"] = 2
    payload.pop("formula")
    payload["source"]["effective_date"] = "2026-01-01"
    payload["source"]["retrieved_at"] = "2026-07-15"
    return payload


def multi_formula_manifest(calculator_id: str = "CUSTOM-MULTI-FORMULA") -> dict:
    payload = schema_v2(calculator_id)
    payload["outputs"] = [
        {"name": "score", "unit": "points", "round": 0},
        {"name": "risk_percent", "unit": "%", "round": 1},
    ]
    payload.pop("output")
    payload["calculation"] = {
        "type": "formula_set",
        "expressions": {
            "score": "amount / 3 if enabled else 0",
            "risk_percent": "amount * 1.234 if mode == 'standard' else amount",
        },
    }
    payload["interpretation"] = [
        {"when": "risk_percent >= 10", "text": "elevated"}
    ]
    payload["default_interpretation"] = "lower"
    payload["test_cases"] = [
        {
            "name": "independent outputs and rounding",
            "inputs": {"amount": 9, "enabled": True, "mode": "standard"},
            "expected_values": {"score": 3, "risk_percent": 11.1},
            "expected_interpretation": "elevated",
        }
    ]
    return payload


def multidimensional_manifest(
    calculator_id: str = "CUSTOM-MULTIDIMENSIONAL-LOOKUP",
) -> dict:
    payload = schema_v2(calculator_id)
    payload["inputs"] = [
        {"name": "sex", "type": "choice", "choices": ["male", "female"]},
        {
            "name": "gestational_age_weeks",
            "type": "number",
            "unit": "weeks",
            "minimum": 20,
            "maximum": 30,
        },
        {
            "name": "birth_weight_g",
            "type": "number",
            "unit": "g",
            "minimum": 300,
            "maximum": 1500,
        },
    ]
    payload["outputs"] = [
        {"name": "score", "unit": "points", "round": 0},
        {"name": "risk_percent", "unit": "%", "round": 1},
    ]
    payload.pop("output")
    payload["calculation"] = {
        "type": "multidimensional_lookup",
        "dimensions": [
            {"input": "sex", "match": "exact"},
            {"input": "gestational_age_weeks", "match": "range"},
            {"input": "birth_weight_g", "match": "range"},
        ],
        "rows": [
            {
                "keys": {
                    "sex": "male",
                    "gestational_age_weeks": {"minimum": 24, "maximum": 26},
                    "birth_weight_g": {"minimum": 500, "maximum": 750},
                },
                "values": {"score": 4, "risk_percent": 10.04},
                "interpretation": "male lower weight band",
            },
            {
                "keys": {
                    "sex": "male",
                    "gestational_age_weeks": {"minimum": 24, "maximum": 26},
                    "birth_weight_g": {
                        "minimum": 750,
                        "maximum": 1000,
                        "include_maximum": True,
                    },
                },
                "values": {"score": 3, "risk_percent": 7.56},
                "interpretation": "male upper weight band",
            },
            {
                "keys": {
                    "sex": "female",
                    "gestational_age_weeks": {"minimum": 24, "maximum": 26},
                    "birth_weight_g": {"minimum": 500, "maximum": 750},
                },
                "values": {"score": 2, "risk_percent": 5},
            },
        ],
    }
    payload["interpretation"] = []
    payload["default_interpretation"] = "matched table row"
    payload["test_cases"] = [
        {
            "name": "shared boundary belongs to upper band",
            "inputs": {
                "sex": "male",
                "gestational_age_weeks": 25,
                "birth_weight_g": 750,
            },
            "expected_values": {"score": 3, "risk_percent": 7.6},
            "expected_interpretation": "male upper weight band",
        }
    ]
    return payload


class CustomExtensionTest(unittest.TestCase):
    def write_manifest(self, directory: Path, payload: dict, name: str = "calculator.json") -> Path:
        path = directory / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_manifest_runs_number_boolean_choice_and_interpretation(self):
        with tempfile.TemporaryDirectory() as temp:
            definition = load_custom_manifest(self.write_manifest(Path(temp), manifest()))
            registry = load_registry(custom_dirs=[temp])
            skill = registry.get(definition.metadata.id)

            result = skill.run({"amount": 20, "enabled": True, "mode": "reduced"})

            self.assertEqual(result.status, "implemented")
            self.assertEqual(result.value, 10)
            self.assertEqual(result.unit, "mg")
            self.assertEqual(result.interpretation, "已计算")
            self.assertFalse(skill.medical_review_check().ok)
            self.assertNotIn(skill, registry.released())

    def test_schema_v2_range_lookup_is_non_interpolating_and_boundary_safe(self):
        with tempfile.TemporaryDirectory() as temp:
            payload = schema_v2("CUSTOM-RANGE-LOOKUP")
            payload["inputs"] = [
                {"name": "score", "type": "number", "unit": "points", "minimum": 0, "maximum": 10}
            ]
            payload["output"] = {"unit": "risk class", "round": 0}
            payload["calculation"] = {
                "type": "lookup_table",
                "input": "score",
                "match": "range",
                "rows": [
                    {"maximum": 5, "value": 1, "interpretation": "lower"},
                    {
                        "minimum": 5,
                        "maximum": 10,
                        "include_maximum": True,
                        "value": 2,
                        "interpretation": "upper",
                    },
                ],
            }
            payload["interpretation"] = []
            payload["default_interpretation"] = "no row"
            payload["test_cases"] = [
                {
                    "name": "boundary belongs to upper row",
                    "inputs": {"score": 5},
                    "expected_value": 2,
                    "expected_interpretation": "upper",
                }
            ]
            definition = load_custom_manifest(self.write_manifest(Path(temp), payload))
            self.assertEqual(definition.implementation(definition.metadata, {"score": 4.9}).value, 1)
            result = definition.implementation(definition.metadata, {"score": 5})
            self.assertEqual(result.value, 2)
            self.assertEqual(result.interpretation, "upper")
            self.assertIn("effective_date=2026-01-01", definition.metadata.notes)
            self.assertIn("retrieved_at=2026-07-15", definition.metadata.notes)

    def test_schema_v2_exact_lookup_supports_declared_choice_keys(self):
        with tempfile.TemporaryDirectory() as temp:
            payload = schema_v2("CUSTOM-EXACT-LOOKUP")
            payload["inputs"] = [
                {"name": "grade", "type": "choice", "choices": ["low", "high"]}
            ]
            payload["output"] = {"unit": "points", "round": 0}
            payload["calculation"] = {
                "type": "lookup_table",
                "input": "grade",
                "match": "exact",
                "rows": [
                    {"key": "low", "value": 0},
                    {"key": "high", "value": 3, "interpretation": "high row"},
                ],
            }
            payload["interpretation"] = []
            payload["default_interpretation"] = "default"
            payload["test_cases"] = [
                {
                    "name": "high grade",
                    "inputs": {"grade": "high"},
                    "expected_value": 3,
                    "expected_interpretation": "high row",
                }
            ]
            definition = load_custom_manifest(self.write_manifest(Path(temp), payload))
            result = definition.implementation(definition.metadata, {"grade": "low"})
            self.assertEqual(result.value, 0)
            self.assertEqual(result.interpretation, "default")

    def test_schema_v2_decision_tree_uses_first_matching_rule(self):
        with tempfile.TemporaryDirectory() as temp:
            payload = schema_v2("CUSTOM-DECISION-TREE")
            payload["inputs"] = [
                {"name": "critical", "type": "boolean"},
                {"name": "score", "type": "number", "unit": "points", "minimum": 0},
            ]
            payload["output"] = {"unit": "decision code", "round": 0}
            payload["calculation"] = {
                "type": "decision_tree",
                "rules": [
                    {"when": "critical", "value": 2, "interpretation": "critical branch"},
                    {"when": "score >= 5", "value": 1, "interpretation": "score branch"},
                ],
                "default": {"value": 0, "interpretation": "default branch"},
            }
            payload["interpretation"] = []
            payload["default_interpretation"] = "unmatched"
            payload["test_cases"] = [
                {
                    "name": "first rule wins",
                    "inputs": {"critical": True, "score": 10},
                    "expected_value": 2,
                    "expected_interpretation": "critical branch",
                }
            ]
            definition = load_custom_manifest(self.write_manifest(Path(temp), payload))
            result = definition.implementation(
                definition.metadata, {"critical": False, "score": 5}
            )
            self.assertEqual(result.value, 1)
            self.assertEqual(result.interpretation, "score branch")

    def test_schema_v2_formula_set_returns_named_rounded_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            payload = multi_formula_manifest()
            definition = load_custom_manifest(self.write_manifest(Path(temp), payload))

            result = definition.implementation(
                definition.metadata,
                {"amount": 6, "enabled": True, "mode": "reduced"},
            )

            self.assertEqual(result.value, {"score": 2.0, "risk_percent": 6.0})
            self.assertEqual(result.unit, "score=points; risk_percent=%")
            self.assertEqual(result.interpretation, "lower")
            self.assertIn("score (points)", definition.metadata.output)

    def test_schema_v2_lookup_and_decision_tree_accept_named_outputs(self):
        lookup = multi_formula_manifest("CUSTOM-MULTI-EXACT-LOOKUP")
        lookup["calculation"] = {
            "type": "lookup_table",
            "input": "mode",
            "match": "exact",
            "rows": [
                {"key": "standard", "values": {"score": 2, "risk_percent": 3.25}},
                {"key": "reduced", "values": {"score": 1, "risk_percent": 1.25}},
            ],
        }
        lookup["test_cases"] = [
            {
                "name": "named exact row",
                "inputs": {"amount": 1, "enabled": True, "mode": "standard"},
                "expected_values": {"score": 2, "risk_percent": 3.2},
            }
        ]

        decision = multi_formula_manifest("CUSTOM-MULTI-DECISION-TREE")
        decision["calculation"] = {
            "type": "decision_tree",
            "rules": [
                {
                    "when": "enabled",
                    "values": {"score": 5, "risk_percent": 12.34},
                    "interpretation": "enabled branch",
                }
            ],
            "default": {"values": {"score": 0, "risk_percent": 0}},
        }
        decision["test_cases"] = [
            {
                "name": "named decision branch",
                "inputs": {"amount": 1, "enabled": True, "mode": "standard"},
                "expected_values": {"score": 5, "risk_percent": 12.3},
                "expected_interpretation": "enabled branch",
            }
        ]

        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for filename, payload in (("lookup.json", lookup), ("decision.json", decision)):
                with self.subTest(filename=filename):
                    definition = load_custom_manifest(
                        self.write_manifest(directory, payload, filename)
                    )
                    self.assertIsInstance(
                        definition.implementation(
                            definition.metadata, payload["test_cases"][0]["inputs"]
                        ).value,
                        dict,
                    )

    def test_schema_v2_multidimensional_lookup_handles_exact_range_and_boundaries(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            payload = multidimensional_manifest()
            definition = load_custom_manifest(self.write_manifest(directory, payload))

            lower = definition.implementation(
                definition.metadata,
                {
                    "sex": "male",
                    "gestational_age_weeks": 24,
                    "birth_weight_g": 749.9,
                },
            )
            boundary = definition.implementation(
                definition.metadata,
                {
                    "sex": "male",
                    "gestational_age_weeks": 25,
                    "birth_weight_g": 750,
                },
            )
            female = definition.implementation(
                definition.metadata,
                {
                    "sex": "female",
                    "gestational_age_weeks": 25,
                    "birth_weight_g": 600,
                },
            )
            unmatched = load_registry(custom_dirs=[directory]).get(payload["id"]).run(
                {
                    "sex": "male",
                    "gestational_age_weeks": 26,
                    "birth_weight_g": 750,
                }
            )

            self.assertEqual(lower.value, {"score": 4.0, "risk_percent": 10.0})
            self.assertEqual(boundary.value, {"score": 3.0, "risk_percent": 7.6})
            self.assertEqual(female.value, {"score": 2.0, "risk_percent": 5.0})
            self.assertEqual(unmatched.status, "invalid_inputs")

    def test_multidimensional_lookup_rejects_only_full_dimension_overlap(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            allowed = multidimensional_manifest("CUSTOM-MULTIDIM-ALLOWED")
            load_custom_manifest(self.write_manifest(directory, allowed, "allowed.json"))

            overlapping = multidimensional_manifest("CUSTOM-MULTIDIM-OVERLAP")
            overlapping["calculation"]["rows"].append(
                {
                    "keys": {
                        "sex": "male",
                        "gestational_age_weeks": {"minimum": 25, "maximum": 27},
                        "birth_weight_g": {"minimum": 700, "maximum": 800},
                    },
                    "values": {"score": 9, "risk_percent": 99},
                }
            )
            with self.assertRaisesRegex(ManifestError, "rows overlap"):
                load_custom_manifest(
                    self.write_manifest(directory, overlapping, "overlapping.json")
                )

    def test_multi_output_manifest_rejects_mismatched_shapes_and_names(self):
        mutations = []

        duplicate = multi_formula_manifest("CUSTOM-BAD-DUPLICATE-OUTPUT")
        duplicate["outputs"][1]["name"] = "score"
        mutations.append((duplicate, "duplicate output name"))

        collision = multi_formula_manifest("CUSTOM-BAD-OUTPUT-COLLISION")
        collision["outputs"][0]["name"] = "amount"
        collision["calculation"]["expressions"] = {
            "amount": "amount",
            "risk_percent": "amount",
        }
        collision["test_cases"][0]["expected_values"] = {
            "amount": 9,
            "risk_percent": 11.1,
        }
        mutations.append((collision, "cannot duplicate input names"))

        missing_expression = multi_formula_manifest("CUSTOM-BAD-MISSING-EXPRESSION")
        del missing_expression["calculation"]["expressions"]["score"]
        mutations.append((missing_expression, "expressions: missing score"))

        scalar_value = multidimensional_manifest("CUSTOM-BAD-SCALAR-VALUE")
        row = scalar_value["calculation"]["rows"][0]
        row["value"] = row.pop("values")["score"]
        mutations.append((scalar_value, "must use values"))

        wrong_expected = multi_formula_manifest("CUSTOM-BAD-EXPECTED-SHAPE")
        case = wrong_expected["test_cases"][0]
        case["expected_value"] = case.pop("expected_values")["score"]
        mutations.append((wrong_expected, "must use expected_values"))

        incomplete_expected = multi_formula_manifest("CUSTOM-BAD-EXPECTED-FIELDS")
        del incomplete_expected["test_cases"][0]["expected_values"]["score"]
        mutations.append((incomplete_expected, "expected_values: missing score"))

        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for index, (payload, message) in enumerate(mutations):
                with self.subTest(message=message):
                    with self.assertRaisesRegex(ManifestError, message):
                        load_custom_manifest(
                            self.write_manifest(directory, payload, f"bad-{index}.json")
                        )

    def test_schema_v2_rejects_overlaps_bad_dates_and_wrong_expected_results(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            missing_cases = schema_v2("CUSTOM-MISSING-CASES")
            missing_cases["calculation"] = {"type": "formula", "expression": "amount"}
            with self.assertRaisesRegex(ManifestError, "requires at least one"):
                load_custom_manifest(
                    self.write_manifest(directory, missing_cases, "missing-cases.json")
                )

            overlapping = schema_v2("CUSTOM-OVERLAP")
            overlapping["inputs"] = [{"name": "score", "type": "number", "unit": "points"}]
            overlapping["output"] = {"unit": "points", "round": 0}
            overlapping["calculation"] = {
                "type": "lookup_table",
                "input": "score",
                "match": "range",
                "rows": [
                    {"minimum": 0, "maximum": 5, "include_maximum": True, "value": 1},
                    {"minimum": 5, "maximum": 10, "value": 2},
                ],
            }
            overlapping["interpretation"] = []
            overlapping["default_interpretation"] = "default"
            overlapping["test_cases"] = [
                {"name": "case", "inputs": {"score": 1}, "expected_value": 1}
            ]
            with self.assertRaisesRegex(ManifestError, "overlap"):
                load_custom_manifest(self.write_manifest(directory, overlapping, "overlap.json"))

            bad_date = schema_v2("CUSTOM-BAD-DATE")
            bad_date["source"]["retrieved_at"] = "15/07/2026"
            bad_date["calculation"] = {
                "type": "formula",
                "expression": "amount if enabled else 0",
            }
            bad_date["test_cases"] = [
                {
                    "name": "case",
                    "inputs": {"amount": 1, "enabled": True, "mode": "standard"},
                    "expected_value": 1,
                }
            ]
            with self.assertRaisesRegex(ManifestError, "ISO date"):
                load_custom_manifest(self.write_manifest(directory, bad_date, "date.json"))

            wrong = schema_v2("CUSTOM-WRONG-EXPECTED")
            wrong["calculation"] = {"type": "formula", "expression": "amount"}
            wrong["test_cases"] = [
                {
                    "name": "wrong",
                    "inputs": {"amount": 1, "enabled": True, "mode": "standard"},
                    "expected_value": 2,
                }
            ]
            with self.assertRaisesRegex(ManifestError, "expected 2"):
                load_custom_manifest(self.write_manifest(directory, wrong, "wrong.json"))

    def test_runtime_validation_rejects_bad_custom_values(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.write_manifest(Path(temp), manifest())
            definition = load_custom_manifest(path)
            registry = load_registry(custom_dirs=[temp])
            skill = registry.get(definition.metadata.id)

            self.assertEqual(
                skill.run({"amount": -1, "enabled": True, "mode": "standard"}).status,
                "invalid_inputs",
            )
            self.assertEqual(
                skill.run({"amount": 1, "enabled": "true", "mode": "standard"}).status,
                "invalid_inputs",
            )
            self.assertEqual(
                skill.run({"amount": 1, "enabled": True, "mode": "other"}).status,
                "invalid_inputs",
            )

    def test_unsafe_expressions_are_rejected(self):
        unsafe = (
            "__import__('os').system('id')",
            "amount.__class__",
            "amount[0]",
            "unknown + 1",
            "2 ** 101",
        )
        with tempfile.TemporaryDirectory() as temp:
            for index, expression in enumerate(unsafe):
                payload = manifest(f"CUSTOM-UNSAFE-{index}")
                payload["formula"]["expression"] = expression
                path = self.write_manifest(Path(temp), payload, f"unsafe-{index}.json")
                with self.assertRaises(ManifestError, msg=expression):
                    load_custom_manifest(path)

    def test_reserved_input_names_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            payload = manifest()
            payload["inputs"][0]["name"] = "sqrt"
            with self.assertRaises(ManifestError):
                load_custom_manifest(self.write_manifest(Path(temp), payload))

    def test_duplicate_custom_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            self.write_manifest(directory, manifest(), "one.json")
            self.write_manifest(directory, manifest(), "two.json")
            with self.assertRaises(ManifestError):
                load_registry(custom_dirs=[directory])

    def test_builtin_id_namespace_cannot_be_used_by_custom_manifests(self):
        with tempfile.TemporaryDirectory() as temp:
            payload = manifest("CALC-0039")
            path = self.write_manifest(Path(temp), payload)
            with self.assertRaises(ManifestError):
                load_custom_manifest(path)

    def test_number_units_and_boundary_flags_are_validated(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            missing_unit = manifest("CUSTOM-NO-UNIT")
            del missing_unit["inputs"][0]["unit"]
            with self.assertRaises(ManifestError):
                load_custom_manifest(self.write_manifest(directory, missing_unit, "unit.json"))

            bad_flag = manifest("CUSTOM-BAD-FLAG")
            bad_flag["inputs"][0]["exclusive_minimum"] = "yes"
            with self.assertRaises(ManifestError):
                load_custom_manifest(self.write_manifest(directory, bad_flag, "flag.json"))

            typo = manifest("CUSTOM-TYPO-FIELD")
            typo["inputs"][0]["exlusive_minimum"] = True
            with self.assertRaises(ManifestError):
                load_custom_manifest(self.write_manifest(directory, typo, "typo.json"))

    def test_cli_scaffold_validate_and_run(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            path = directory / "new.json"
            scaffold = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "scaffold",
                    "--output",
                    str(path),
                    "--id",
                    "CUSTOM-CLI-TEST",
                    "--name-cn",
                    "CLI 测试",
                    "--name-en",
                    "CLI Test",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(scaffold.returncode, 0, scaffold.stderr)

            validate = subprocess.run(
                [sys.executable, str(CLI), "validate-custom", str(path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validate.returncode, 0, validate.stdout)

            run = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "--custom-dir",
                    str(directory),
                    "run",
                    "CUSTOM-CLI-TEST",
                    "--input",
                    "weight_kg=70",
                    "--input",
                    "height_cm=175",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(run.returncode, 0, run.stdout)
            self.assertEqual(json.loads(run.stdout)["result"]["value"], 22.86)

    def test_cli_scaffolds_all_schema_v2_calculation_shapes(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            cases = (
                ("lookup", "CUSTOM-CLI-LOOKUP", "lookup.json"),
                ("decision-tree", "CUSTOM-CLI-TREE", "tree.json"),
                ("multi-formula", "CUSTOM-CLI-MULTI-FORMULA", "multi-formula.json"),
                ("multi-lookup", "CUSTOM-CLI-MULTI-LOOKUP", "multi-lookup.json"),
            )
            for kind, calculator_id, filename in cases:
                with self.subTest(kind=kind):
                    path = directory / filename
                    scaffold = subprocess.run(
                        [
                            sys.executable,
                            str(CLI),
                            "scaffold",
                            "--kind",
                            kind,
                            "--output",
                            str(path),
                            "--id",
                            calculator_id,
                            "--name-cn",
                            f"{kind} 测试",
                            "--name-en",
                            f"{kind} test",
                        ],
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(scaffold.returncode, 0, scaffold.stdout)
                    payload = json.loads(path.read_text())
                    self.assertEqual(payload["schema_version"], 2)
                    self.assertTrue(payload["test_cases"])
                    if kind.startswith("multi-"):
                        self.assertEqual(len(payload["outputs"]), 2)
                        self.assertIn("expected_values", payload["test_cases"][0])
                    validate = subprocess.run(
                        [sys.executable, str(CLI), "validate-custom", str(path)],
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(validate.returncode, 0, validate.stdout)

    def test_cli_backlog_ranks_all_source_candidates_and_filters(self):
        full = subprocess.run(
            [sys.executable, str(CLI), "backlog", "--limit", "110"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        filtered = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "backlog",
                "--blocker",
                "reference_tables_needed",
                "--limit",
                "10",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(full.returncode, 0, full.stdout)
        payload = json.loads(full.stdout)
        self.assertEqual(payload["candidate_count"], 110)
        self.assertEqual(payload["returned_count"], 110)
        self.assertEqual(payload["queue"][0]["priority_tier"], 3)
        self.assertEqual(payload["queue"][-1]["priority_tier"], 6)
        self.assertEqual([item["rank"] for item in payload["queue"]], list(range(1, 111)))
        self.assertTrue(
            all(
                item["source_url"] and item["data_needed"] and item["next_action"]
                for item in payload["queue"]
            )
        )

        self.assertEqual(filtered.returncode, 0, filtered.stdout)
        filtered_payload = json.loads(filtered.stdout)
        self.assertEqual(filtered_payload["candidate_count"], 5)
        self.assertEqual(filtered_payload["queue"][0]["id"], "CALC-0516")

    def test_cli_search_defaults_to_executable_and_exposes_catalog_layers(self):
        default = subprocess.run(
            [sys.executable, str(CLI), "search", "CRIB-II"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        all_entries = subprocess.run(
            [sys.executable, str(CLI), "search", "CRIB-II", "--all"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        candidate = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "search",
                "CRIB-II",
                "--layer",
                "source_candidate",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(default.returncode, 0, default.stdout)
        self.assertEqual(json.loads(default.stdout)["count"], 0)
        all_payload = json.loads(all_entries.stdout)
        self.assertEqual(all_payload["count"], 1)
        self.assertEqual(all_payload["results"][0]["catalog_layer"], "source_candidate")
        self.assertEqual(json.loads(candidate.stdout)["results"][0]["id"], "CALC-0771")

    def test_cli_install_makes_manifest_discoverable(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source = directory / "source.json"
            destination = directory / "installed"
            self.write_manifest(directory, manifest("CUSTOM-INSTALL-TEST"), source.name)

            install = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "install-custom",
                    str(source),
                    "--destination",
                    str(destination),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(install.returncode, 0, install.stdout)
            installed = destination / "custom-install-test.json"
            self.assertTrue(installed.exists())
            self.assertEqual(load_registry(custom_dirs=[destination]).get("CUSTOM-INSTALL-TEST").metadata.id, "CUSTOM-INSTALL-TEST")

    def test_cli_install_refuses_placeholder_source_draft(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            payload = manifest("CUSTOM-PLACEHOLDER-DRAFT")
            payload["source"]["name"] = "Replace with a primary source"
            payload["source"]["url"] = "https://example.org/replace-with-source"
            payload["source"]["version"] = "replace-with-version"
            source = self.write_manifest(directory, payload)
            destination = directory / "installed"

            install = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "install-custom",
                    str(source),
                    "--destination",
                    str(destination),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(install.returncode, 2, install.stdout)
            self.assertIn("placeholder source metadata", install.stdout)
            self.assertFalse((destination / "custom-placeholder-draft.json").exists())

    def test_default_registry_baseline_is_unchanged(self):
        summary = load_registry(include_custom=False).summary()
        self.assertEqual(summary["total_rows"], 1054)
        self.assertEqual(summary["inventory_rows"], 1138)
        self.assertEqual(summary["merged_alias_rows"], 84)
        self.assertEqual(summary["implemented_rows"], 643)
        self.assertEqual(summary["implemented_unique_names"], 570)
        self.assertEqual(summary["metadata_only_rows"], 411)


if __name__ == "__main__":
    unittest.main()
