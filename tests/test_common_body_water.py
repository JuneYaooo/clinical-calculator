import unittest

from clinical_calculators.calculators.common.body_water import (
    female_total_body_water_watson_formula,
    free_water_deficit_hypernatremia,
    lean_body_weight_female_janmahasatian,
    lean_body_weight_male_janmahasatian,
    male_total_body_water_watson_formula,
    serum_ascites_albumin_gradient,
    total_body_water_estimate_by_weight,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="body water",
        scenario="unit test",
        name_cn=name_cn,
        name_en=name_cn,
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


class CommonBodyWaterCalculatorsTest(unittest.TestCase):
    def test_saag_subtracts_ascites_albumin_and_flags_portal_pattern(self):
        result = serum_ascites_albumin_gradient(
            metadata("腹水白蛋白梯度"),
            {"serum_albumin_g_dl": 3.0, "ascites_albumin_g_dl": 1.0},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 2.0, places=4)
        self.assertEqual(result.unit, "g/dL")
        self.assertIn("portal hypertension", result.interpretation)

    def test_total_body_water_by_weight_uses_default_fraction(self):
        result = total_body_water_estimate_by_weight(
            metadata("基于体重的体内总水量估计"),
            {"weight_kg": 70},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 42.0, places=4)
        self.assertEqual(result.unit, "L")

    def test_female_watson_total_body_water_uses_height_and_weight(self):
        result = female_total_body_water_watson_formula(
            metadata("女性体内总水量（沃森公式）"),
            {"height_cm": 165, "weight_kg": 60, "age_years": 50},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 30.3375, places=4)
        self.assertEqual(result.unit, "L")

    def test_male_watson_total_body_water_uses_age_height_and_weight(self):
        result = male_total_body_water_watson_formula(
            metadata("男性体内总水量（沃森公式）"),
            {"height_cm": 175, "weight_kg": 70, "age_years": 50},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 40.018, places=4)
        self.assertEqual(result.unit, "L")

    def test_free_water_deficit_uses_total_body_water_fraction(self):
        result = free_water_deficit_hypernatremia(
            metadata("高钠血症时的缺水程度"),
            {
                "weight_kg": 70,
                "current_sodium_mEq_l": 160,
                "target_sodium_mEq_l": 140,
                "total_body_water_fraction": 0.6,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 6.0, places=4)
        self.assertEqual(result.unit, "L")
        self.assertIn("clinical monitoring", result.interpretation)

    def test_female_janmahasatian_lean_body_weight_uses_bmi(self):
        result = lean_body_weight_female_janmahasatian(
            metadata("净体重（女）"),
            {"height_cm": 165, "weight_kg": 60},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 39.2868, places=4)
        self.assertEqual(result.unit, "kg")

    def test_male_janmahasatian_lean_body_weight_uses_bmi(self):
        result = lean_body_weight_male_janmahasatian(
            metadata("净体重（男）"),
            {"height_cm": 175, "weight_kg": 70},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 55.8571, places=4)
        self.assertEqual(result.unit, "kg")


if __name__ == "__main__":
    unittest.main()
