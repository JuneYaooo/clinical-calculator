import unittest

from clinical_calculators.calculators.common.hepatology_scores import (
    apri_index,
    autoimmune_hepatitis_simplified_diagnostic_criteria,
    bisap_acute_pancreatitis_score,
    child_pugh_classification,
    fib_4_index,
    lille_model_alcoholic_hepatitis,
    maddrey_discriminant_function,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=f"test-{name_en.lower().replace(' ', '-')}",
        category="common",
        subspecialty="hepatology",
        scenario="unit test",
        name_cn=name_cn,
        name_en=name_en,
        inputs="",
        output="",
        formula="",
        interpretation="",
        purpose="",
        source_type="",
        source="",
        source_url="",
        channel="",
        evidence_tier="",
        commonness="",
        coverage_note="",
        clinical_note="",
        version="",
        entry_source="",
        source_group="",
        notes="",
    )


class CommonHepatologyScoresTest(unittest.TestCase):
    def test_apri_ast80_uln40_platelets100_scores_two(self):
        calculation = apri_index(
            metadata("APRI指数", "APRI Index"),
            {"ast_u_l": 80, "ast_uln_u_l": 40, "platelets_10e9_l": 100},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 2.0)
        self.assertEqual(calculation.unit, "index")

    def test_fib_4_age50_ast80_alt40_platelets200_scores_3_1623_and_high(self):
        calculation = fib_4_index(
            metadata("FIB-4指数", "FIB-4 Index"),
            {"age_years": 50, "ast_u_l": 80, "alt_u_l": 40, "platelets_10e9_l": 200},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value, 3.1623, places=4)
        self.assertEqual(calculation.unit, "index")
        self.assertIn("high", calculation.interpretation)

    def test_maddrey_pt20_control12_bilirubin10_scores_46_8_and_severe(self):
        calculation = maddrey_discriminant_function(
            metadata(
                "糖皮质激素治疗酒精性肝炎的肝炎判别函数",
                "Maddrey Discriminant Function",
            ),
            {
                "prothrombin_time_seconds": 20,
                "control_prothrombin_time_seconds": 12,
                "bilirubin_mg_dl": 10,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 46.8)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("severe alcoholic hepatitis", calculation.interpretation)

    def test_child_pugh_scores_ten_and_class_c(self):
        calculation = child_pugh_classification(
            metadata("肝病严重程度的Child Pugh分类", "Child-Pugh Classification"),
            {
                "bilirubin_mg_dl": 2.5,
                "albumin_g_dl": 3.0,
                "inr": 2.0,
                "ascites": "mild",
                "encephalopathy": "grade_1_2",
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 10)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("Class C", calculation.interpretation)

    def test_bisap_scores_all_five_criteria(self):
        calculation = bisap_acute_pancreatitis_score(
            metadata("BISAP急性胰腺炎评分", "BISAP Score for Acute Pancreatitis"),
            {
                "bun_mg_dl": 30,
                "impaired_mental_status": True,
                "sirs": True,
                "age_years": 70,
                "pleural_effusion": True,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value, 5)
        self.assertEqual(calculation.unit, "points")

    def test_child_pugh_rejects_unknown_ascites_category(self):
        with self.assertRaises(ValueError):
            child_pugh_classification(
                metadata("肝病严重程度的Child Pugh分类", "Child-Pugh Classification"),
                {
                    "bilirubin_mg_dl": 2.5,
                    "albumin_g_dl": 3.0,
                    "inr": 2.0,
                    "ascites": "large",
                    "encephalopathy": "grade_1_2",
                },
            )

    def test_bisap_rejects_non_boolean_flags(self):
        with self.assertRaises(ValueError):
            bisap_acute_pancreatitis_score(
                metadata("BISAP急性胰腺炎评分", "BISAP Score for Acute Pancreatitis"),
                {
                    "bun_mg_dl": 30,
                    "impaired_mental_status": "yes",
                    "sirs": True,
                    "age_years": 70,
                    "pleural_effusion": True,
                },
            )

    def test_lille_model_uses_published_logistic_formula(self):
        calculation = lille_model_alcoholic_hepatitis(
            metadata("Lille模型", "Lille Model"),
            {
                "age_years": 50,
                "albumin_g_l": 30,
                "bilirubin_day0_umol_l": 300,
                "bilirubin_day7_umol_l": 250,
                "prothrombin_time_seconds": 20,
                "renal_insufficiency": False,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value, 0.2257, places=4)
        self.assertEqual(calculation.unit, "probability")
        self.assertIn("responder", calculation.interpretation)

    def test_autoimmune_hepatitis_simplified_criteria_uses_prescored_components(self):
        calculation = autoimmune_hepatitis_simplified_diagnostic_criteria(
            metadata("自身免疫性肝炎诊断标准", "Autoimmune Hepatitis Diagnostic Criteria"),
            {
                "autoantibodies": 2,
                "igg": 2,
                "liver_histology": 2,
                "viral_hepatitis_absent": 2,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertEqual(calculation.value["score"], 8)
        self.assertTrue(calculation.value["definite_autoimmune_hepatitis"])
        self.assertIn("definite", calculation.interpretation)

    def test_autoimmune_hepatitis_rejects_invalid_component_points(self):
        with self.assertRaises(ValueError):
            autoimmune_hepatitis_simplified_diagnostic_criteria(
                metadata("自身免疫性肝炎诊断标准", "Autoimmune Hepatitis Diagnostic Criteria"),
                {
                    "autoantibodies": 3,
                    "igg": 2,
                    "liver_histology": 2,
                    "viral_hepatitis_absent": 2,
                },
            )


if __name__ == "__main__":
    unittest.main()
