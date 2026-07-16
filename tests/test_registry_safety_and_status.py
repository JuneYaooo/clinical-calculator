import unittest

from clinical_calculators import load_registry


class RegistrySafetyAndStatusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_registry()

    def test_registry_reports_auditable_implementation_levels(self):
        summary = self.registry.summary()

        self.assertEqual(
            set(summary["implementation_levels"]),
            {"complete", "partial", "metadata_only", "licensed_rule"},
        )
        self.assertTrue(all(count > 0 for count in summary["implementation_levels"].values()))
        self.assertEqual(sum(summary["implementation_levels"].values()), summary["total_rows"])
        self.assertGreater(summary["ambiguous_name_groups"], 0)
        self.assertGreaterEqual(summary["versioned_rows"], 2)
        self.assertGreaterEqual(summary["medical_review_ready_rows"], 1)
        self.assertEqual(summary["released_rows"], 0)
        self.assertEqual(self.registry.get("CALC-0039").implementation_level, "complete")
        self.assertEqual(self.registry.get("CALC-0004").implementation_level, "partial")
        self.assertEqual(self.registry.get("CALC-0459").implementation_level, "licensed_rule")

    def test_medical_review_check_exposes_source_governance_gaps(self):
        generic = self.registry.get("CALC-0039").medical_review_check()
        versioned = self.registry.get("CALC-0705").medical_review_check()

        self.assertFalse(generic.ok)
        self.assertIn("missing source version/year", generic.errors)
        self.assertTrue(versioned.ok)

    def test_get_all_excludes_exact_duplicates_merged_as_aliases(self):
        variants = self.registry.get_all("QT间期校正 (EKG)")

        self.assertEqual([skill.metadata.id for skill in variants], ["CALC-0031"])
        qt_aliases = {
            alias_id: target
            for alias_id, (target, _) in self.registry.aliases.items()
            if target == "CALC-0031"
        }
        self.assertEqual(len(qt_aliases), 13)

    def test_runtime_backlog_and_release_views_are_separated(self):
        self.assertEqual(len(self.registry.runnable()), self.registry.summary()["implemented_rows"])
        self.assertEqual(len(self.registry.backlog()), self.registry.summary()["metadata_only_rows"])
        self.assertEqual(len(self.registry.released()), 0)
        self.assertGreaterEqual(len(self.registry.automated_review_ready()), 4)
        self.assertTrue(self.registry.search_runnable("DLCN"))
        self.assertFalse(self.registry.search_released("DLCN"))

    def test_input_schema_exposes_type_unit_and_bounds(self):
        bmi = self.registry.get("CALC-0039")

        self.assertEqual([spec.name for spec in bmi.input_schema], ["weight_kg", "height_cm"])
        self.assertEqual([spec.unit for spec in bmi.input_schema], ["kg", "cm"])
        self.assertTrue(all(spec.value_type == "number" for spec in bmi.input_schema))

    def test_run_distinguishes_missing_invalid_and_unimplemented(self):
        missing = self.registry.get("CALC-0039").run({"weight_kg": 70})
        invalid = self.registry.get("CALC-0039").run({"weight_kg": -70, "height_cm": 175})
        unavailable = self.registry.get("CALC-0053").run({})

        self.assertEqual(missing.status, "missing_inputs")
        self.assertEqual(invalid.status, "invalid_inputs")
        self.assertEqual(unavailable.status, "needs_formula_implementation")

    def test_run_rejects_nonfinite_numbers_and_invalid_boolean_strings(self):
        nan_bmi = self.registry.get("CALC-0039").run({"weight_kg": "nan", "height_cm": 175})
        phenytoin = self.registry.get("CALC-1070").run(
            {"measured_total_phenytoin_mcg_ml": 10, "albumin_g_dl": 3, "renal_failure": "false"}
        )

        self.assertEqual(nan_bmi.status, "invalid_inputs")
        self.assertEqual(phenytoin.status, "invalid_inputs")

    def test_pediatric_bmi_row_no_longer_returns_adult_interpretation(self):
        calculation = self.registry.get("CALC-0234").run(
            {"age_years": 10, "weight_kg": 40, "height_cm": 140}
        )

        self.assertEqual(calculation.status, "partial")
        self.assertAlmostEqual(calculation.value, 20.4082, places=4)
        self.assertIn("Do not apply adult BMI categories", calculation.interpretation)

    def test_z_score_percentile_rows_match_their_metadata_input(self):
        calculation = self.registry.get("CALC-0233").run({"z_score": 1})

        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value, 84.1345, places=4)


if __name__ == "__main__":
    unittest.main()
