import unittest

from clinical_calculators.calculators.common.surgery_liver_more import (
    abc_massive_transfusion_score,
    albi_grade,
    bard_nafld_fibrosis_score,
    nafld_fibrosis_score,
    obesity_surgery_mortality_risk_score,
    palbi_grade,
    revised_baux_score,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str = "calculator") -> CalculatorMetadata:
    return CalculatorMetadata(
        id=f"test-{name_cn}",
        category="common",
        subspecialty="",
        scenario="",
        name_cn=name_cn,
        name_en="Calculator",
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


class CommonSurgeryLiverMoreTest(unittest.TestCase):
    def test_revised_baux_score_adds_age_tbsa_and_inhalation_penalty(self):
        result = revised_baux_score(
            metadata("修订Baux评分"), {"age_years": 50, "tbsa_burn_percent": 40, "inhalation_injury": True}
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 107)
        self.assertEqual(result.unit, "points")

    def test_abc_massive_transfusion_score_counts_four_binary_items(self):
        result = abc_massive_transfusion_score(
            metadata("ABC大量输血评分"),
            {"penetrating_mechanism": True, "positive_fast": True, "systolic_bp": 90, "heart_rate": 120},
        )

        self.assertEqual(result.value, 4)
        self.assertIn("higher", result.interpretation)

    def test_obesity_surgery_mortality_risk_score_and_class(self):
        result = obesity_surgery_mortality_risk_score(
            metadata("代谢手术死亡风险OS-MRS"),
            {
                "bmi": 52,
                "male": True,
                "hypertension": True,
                "pulmonary_embolism_risk": False,
                "age_years": 46,
            },
        )

        self.assertEqual(result.value, 4)
        self.assertIn("class C", result.interpretation)

    def test_albi_score_and_grade(self):
        result = albi_grade(metadata("ALBI白蛋白胆红素评分"), {"bilirubin_umol_l": 20, "albumin_g_l": 40})

        self.assertAlmostEqual(result.value, -2.5413, places=4)
        self.assertIn("grade 2", result.interpretation)

    def test_palbi_score_and_grade(self):
        result = palbi_grade(
            metadata("PALBI血小板白蛋白胆红素评分"),
            {"bilirubin_umol_l": 20, "albumin_g_l": 40, "platelets_10e9_l": 150},
        )

        self.assertAlmostEqual(result.value, -2.3883, places=4)
        self.assertIn("grade 2", result.interpretation)

    def test_nafld_fibrosis_score(self):
        result = nafld_fibrosis_score(
            metadata("NAFLD纤维化评分"),
            {
                "age_years": 50,
                "bmi": 30,
                "impaired_fasting_glucose_or_diabetes": True,
                "ast_u_l": 60,
                "alt_u_l": 40,
                "platelets_10e9_l": 200,
                "albumin_g_dl": 4.0,
            },
        )

        self.assertAlmostEqual(result.value, 0.37, places=4)
        self.assertIn("indeterminate", result.interpretation)

    def test_bard_nafld_fibrosis_score(self):
        result = bard_nafld_fibrosis_score(
            metadata("BARD脂肪肝纤维化评分"), {"bmi": 30, "ast_u_l": 40, "alt_u_l": 40, "diabetes": True}
        )

        self.assertEqual(result.value, 4)
        self.assertIn("higher", result.interpretation)


if __name__ == "__main__":
    unittest.main()
