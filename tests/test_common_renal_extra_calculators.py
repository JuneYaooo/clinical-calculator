import unittest

from clinical_calculators.calculators.common import renal
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="renal",
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


class CommonRenalExtraCalculatorsTest(unittest.TestCase):
    def test_fractional_excretion_sodium_uses_concentration_ratio(self):
        self.assertTrue(hasattr(renal, "fractional_excretion_sodium"))

        result = renal.fractional_excretion_sodium(
            metadata("Na排泄分数"),
            {
                "urine_sodium_mEq_l": 40,
                "serum_sodium_mEq_l": 140,
                "urine_creatinine_mg_dl": 100,
                "serum_creatinine_mg_dl": 1,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 0.2857, places=4)
        self.assertEqual(result.unit, "%")

    def test_fractional_excretion_sodium_si_uses_same_ratio(self):
        self.assertTrue(hasattr(renal, "fractional_excretion_sodium_si"))

        result = renal.fractional_excretion_sodium_si(
            metadata("Na排泄分数（SI单位）"),
            {
                "urine_sodium_mmol_l": 40,
                "serum_sodium_mmol_l": 140,
                "urine_creatinine_umol_l": 10000,
                "serum_creatinine_umol_l": 100,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 0.2857, places=4)
        self.assertEqual(result.unit, "%")

    def test_fractional_excretion_urea_uses_urea_creatinine_ratio(self):
        self.assertTrue(hasattr(renal, "fractional_excretion_urea"))

        result = renal.fractional_excretion_urea(
            metadata("尿素排泄分数"),
            {
                "urine_urea_mg_dl": 500,
                "serum_urea_mg_dl": 50,
                "urine_creatinine_mg_dl": 100,
                "serum_creatinine_mg_dl": 1,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 10.0, places=4)
        self.assertEqual(result.unit, "%")

    def test_sodium_deficit_hyponatremia_uses_total_body_water_fraction(self):
        self.assertTrue(hasattr(renal, "sodium_deficit_hyponatremia"))

        result = renal.sodium_deficit_hyponatremia(
            metadata("低钠血症的钠缺乏"),
            {
                "weight_kg": 70,
                "current_sodium_mEq_l": 125,
                "target_sodium_mEq_l": 135,
                "total_body_water_fraction": 0.6,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 420.0, places=4)
        self.assertEqual(result.unit, "mEq")
        self.assertIn("clinically supervised", result.interpretation)

    def test_parkland_formula_adult_returns_first_24_hour_lactated_ringers(self):
        self.assertTrue(hasattr(renal, "parkland_formula_adult"))

        result = renal.parkland_formula_adult(
            metadata("烧伤液体复苏，成人（Parkland公式）"),
            {"weight_kg": 70, "tbsa_burn_percent": 30},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 8400.0, places=4)
        self.assertEqual(result.unit, "mL")
        self.assertIn("first 8h", result.interpretation)


if __name__ == "__main__":
    unittest.main()
