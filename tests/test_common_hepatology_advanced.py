import unittest

from clinical_calculators.calculators.common.hepatology_advanced import (
    baveno_vi_varices_risk_criteria,
    clif_c_aclf_score,
    clif_c_ad_score,
    meld_3_score,
    meld_na_score,
    peld_score,
    ranson_acute_pancreatitis_criteria,
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


class CommonHepatologyAdvancedTest(unittest.TestCase):
    def test_meld_na_scores_exact_formula_value(self):
        calculation = meld_na_score(
            metadata("终末期肝病MELDNa评分（不适合12岁以下患者）", "MELD-Na Score"),
            {
                "bilirubin_mg_dl": 3,
                "inr": 2,
                "creatinine_mg_dl": 1.5,
                "sodium_mEq_l": 130,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value, 26.3320, places=4)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("adult MELD-Na", calculation.interpretation)
        self.assertIn("not for patients younger than 12 years", calculation.interpretation)

    def test_meld_na_dialysis_forces_creatinine_to_four(self):
        calculation = meld_na_score(
            metadata("终末期肝病MELDNa评分（不适合12岁以下患者）", "MELD-Na Score"),
            {
                "bilirubin_mg_dl": 3,
                "inr": 2,
                "creatinine_mg_dl": 0.4,
                "sodium_mEq_l": 130,
                "dialysis_twice_in_last_week": True,
            },
        )

        self.assertAlmostEqual(calculation.value, 33.5503, places=4)
        self.assertEqual(calculation.unit, "points")

    def test_meld_3_score_uses_optn_formula_components(self):
        calculation = meld_3_score(
            metadata("MELD 3.0评分", "MELD 3.0 Score"),
            {
                "bilirubin_mg_dl": 3,
                "inr": 2,
                "creatinine_mg_dl": 1.5,
                "sodium_mEq_l": 130,
                "albumin_g_dl": 3.0,
                "sex": "female",
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value, 27.6056, places=4)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("MELD 3.0", calculation.interpretation)

    def test_meld_3_dialysis_caps_creatinine_to_three(self):
        calculation = meld_3_score(
            metadata("MELD 3.0评分", "MELD 3.0 Score"),
            {
                "bilirubin_mg_dl": 1,
                "inr": 1,
                "creatinine_mg_dl": 0.6,
                "sodium_mEq_l": 137,
                "albumin_g_dl": 3.5,
                "sex": "male",
                "dialysis_twice_in_last_week": True,
            },
        )

        self.assertAlmostEqual(calculation.value, 18.2385, places=4)

    def test_peld_scores_exact_formula_value(self):
        calculation = peld_score(
            metadata("PELD评分", "PELD Score"),
            {
                "age_years": 0.5,
                "albumin_g_dl": 3,
                "bilirubin_mg_dl": 2,
                "inr": 1.5,
                "growth_failure": True,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value, 14.3391, places=4)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("pediatric liver disease score", calculation.interpretation)

    def test_ranson_scores_all_criteria_positive(self):
        calculation = ranson_acute_pancreatitis_criteria(
            metadata("Ranson急性胰腺炎标准", "Ranson Criteria for Acute Pancreatitis"),
            {
                "age_years": 56,
                "wbc_10e9_l": 17,
                "glucose_mg_dl": 201,
                "ast_u_l": 251,
                "ldh_u_l": 351,
                "hematocrit_fall_percent": 11,
                "bun_increase_mg_dl": 6,
                "calcium_mg_dl": 7.9,
                "pao2_mm_hg": 59,
                "base_deficit_mEq_l": 5,
                "fluid_sequestration_l": 7,
            },
        )

        self.assertEqual(calculation.value, 11)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("higher score", calculation.interpretation)

    def test_ranson_scores_all_criteria_negative(self):
        calculation = ranson_acute_pancreatitis_criteria(
            metadata("Ranson急性胰腺炎标准", "Ranson Criteria for Acute Pancreatitis"),
            {
                "age_years": 55,
                "wbc_10e9_l": 16,
                "glucose_mg_dl": 200,
                "ast_u_l": 250,
                "ldh_u_l": 350,
                "hematocrit_fall_percent": 10,
                "bun_increase_mg_dl": 5,
                "calcium_mg_dl": 8,
                "pao2_mm_hg": 60,
                "base_deficit_mEq_l": 4,
                "fluid_sequestration_l": 6,
            },
        )

        self.assertEqual(calculation.value, 0)
        self.assertEqual(calculation.unit, "points")

    def test_clif_c_aclf_uses_prescored_clif_organ_failure_age_and_wbc(self):
        calculation = clif_c_aclf_score(
            metadata("CLIF-C ACLF评分", "CLIF-C ACLF Score"),
            {"clif_c_of_score": 12, "age_years": 60, "wbc_10e9_l": 10},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value, 58.1063, places=4)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("ACLF", calculation.interpretation)

    def test_clif_c_aclf_rejects_out_of_range_organ_failure_score(self):
        with self.assertRaises(ValueError):
            clif_c_aclf_score(
                metadata("CLIF-C ACLF评分", "CLIF-C ACLF Score"),
                {"clif_c_of_score": 5, "age_years": 60, "wbc_10e9_l": 10},
            )

    def test_clif_c_ad_uses_age_creatinine_inr_wbc_and_sodium(self):
        calculation = clif_c_ad_score(
            metadata("CLIF-C AD评分", "CLIF-C AD Score"),
            {
                "age_years": 60,
                "creatinine_mg_dl": 1.5,
                "inr": 1.6,
                "wbc_10e9_l": 10,
                "sodium_mEq_l": 130,
            },
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value, 63.9759, places=4)
        self.assertEqual(calculation.unit, "points")
        self.assertIn("acute decompensation", calculation.interpretation)

    def test_baveno_vi_identifies_low_risk_varices_case_that_can_avoid_screening_endoscopy(self):
        calculation = baveno_vi_varices_risk_criteria(
            metadata("Baveno VI门静脉高压静脉曲张风险", "Baveno VI Varices Risk Criteria"),
            {"liver_stiffness_kpa": 18, "platelets_10e9_l": 160},
        )

        self.assertEqual(calculation.status, "implemented")
        self.assertTrue(calculation.value["can_avoid_screening_endoscopy"])
        self.assertEqual(calculation.unit, "classification")
        self.assertIn("low risk", calculation.interpretation)


if __name__ == "__main__":
    unittest.main()
