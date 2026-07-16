import unittest

from clinical_calculators.calculators.common.misc_formula_more import (
    age_adjusted_mac,
    bang_diabetes_risk_score,
    corrected_csf_protein_traumatic_tap,
    mifflin_st_jeor_resting_energy_expenditure,
    pet_total_lesion_glycolysis,
    platelet_corrected_count_increment,
    risk_percent_from_log_odds,
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


class CommonMiscFormulaMoreTest(unittest.TestCase):
    def test_risk_percent_from_log_odds(self):
        result = risk_percent_from_log_odds(metadata("在吸烟者和既往吸烟者（6年）中患肺癌的风险评估"), {"log_odds": 0})

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 50)
        self.assertEqual(result.unit, "%")

    def test_bang_diabetes_risk_score_source_boundaries(self):
        high_risk = bang_diabetes_risk_score(
            metadata("糖尿病风险自我评估"),
            {
                "age_years": 60,
                "sex": "male",
                "bmi": 40,
                "family_history_diabetes": True,
                "hypertension": True,
                "physically_active": False,
            },
        )
        low_risk = bang_diabetes_risk_score(
            metadata("糖尿病风险自我评估"),
            {
                "age_years": 39,
                "sex": "female",
                "bmi": 24.9,
                "family_history_diabetes": False,
                "hypertension": False,
                "physically_active": True,
            },
        )

        self.assertEqual(high_risk.value, 9)
        self.assertIn("score >=5", high_risk.interpretation)
        self.assertEqual(low_risk.value, -1)
        self.assertEqual(high_risk.unit, "points")

    def test_bang_diabetes_risk_score_rejects_outside_validated_age(self):
        with self.assertRaisesRegex(ValueError, "at least 20"):
            bang_diabetes_risk_score(
                metadata("糖尿病风险自我评估"),
                {
                    "age_years": 19,
                    "sex": "female",
                    "bmi": 25,
                    "family_history_diabetes": False,
                    "hypertension": False,
                    "physically_active": False,
                },
            )

    def test_corrected_csf_protein_traumatic_tap(self):
        result = corrected_csf_protein_traumatic_tap(
            metadata("血液污染脑脊液的蛋白浓度校正"),
            {
                "csf_protein_mg_dl": 100,
                "serum_protein_g_dl": 7,
                "hematocrit_percent": 45,
                "csf_rbc_per_uL": 100000,
                "blood_rbc_10e6_per_uL": 5,
            },
        )

        self.assertAlmostEqual(result.value, 23, places=4)
        self.assertEqual(result.unit, "mg/dL")

    def test_pet_total_lesion_glycolysis(self):
        result = pet_total_lesion_glycolysis(metadata("PET代谢肿瘤体积和总病灶糖酵解"), {"mtv_ml": 20, "suv_mean": 5})

        self.assertEqual(result.value, 100)
        self.assertEqual(result.unit, "SUV*ml")

    def test_platelet_corrected_count_increment(self):
        result = platelet_corrected_count_increment(
            metadata("血小板输注校正增量"),
            {"platelet_increment_10e9_l": 30, "body_surface_area_m2": 1.8, "platelets_transfused_10e11": 3},
        )

        self.assertEqual(result.value, 18)
        self.assertEqual(result.unit, "CCI")

    def test_mifflin_st_jeor_resting_energy_expenditure(self):
        male = mifflin_st_jeor_resting_energy_expenditure(
            metadata("Mifflin-St Jeor静息能量消耗"), {"sex": "male", "weight_kg": 70, "height_cm": 175, "age_years": 40}
        )
        female = mifflin_st_jeor_resting_energy_expenditure(
            metadata("Mifflin-St Jeor静息能量消耗"), {"sex": "female", "weight_kg": 70, "height_cm": 175, "age_years": 40}
        )

        self.assertEqual(male.value, 1598.75)
        self.assertEqual(female.value, 1432.75)

    def test_age_adjusted_mac(self):
        result = age_adjusted_mac(metadata("年龄校正MAC"), {"mac_at_40": 1.17, "age_years": 80, "target_mac_fraction": 1})

        self.assertAlmostEqual(result.value, 0.9132, places=4)
        self.assertEqual(result.unit, "MAC")


if __name__ == "__main__":
    unittest.main()
