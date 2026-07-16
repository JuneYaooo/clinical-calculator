import unittest

from clinical_calculators.calculators.common.acidbase_renal_more import (
    anion_gap_delta,
    bicarbonate_delta,
    delta_delta_gradient,
    female_urea_distribution_volume_watson,
    male_urea_distribution_volume_watson,
    serum_anion_gap_for_delta_delta,
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


class CommonAcidbaseRenalMoreTest(unittest.TestCase):
    def test_delta_delta_gradient_subtracts_delta_bicarbonate_from_delta_gap(self):
        result = delta_delta_gradient(
            metadata("阴离子间隙Delta Delta 梯度Multicalc"),
            {"delta_gap_mEq_l": 10, "delta_bicarbonate_mEq_l": 8},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 2)
        self.assertEqual(result.unit, "mEq/L")

    def test_bicarbonate_delta_uses_25_minus_bicarbonate(self):
        result = bicarbonate_delta(
            metadata("阴离子间隙Delta Delta 梯度Multicalc"),
            {"bicarbonate_mEq_l": 15},
        )

        self.assertEqual(result.value, 10)
        self.assertEqual(result.unit, "mEq/L")

    def test_serum_anion_gap_for_delta_delta_uses_sodium_chloride_bicarbonate(self):
        result = serum_anion_gap_for_delta_delta(
            metadata("阴离子间隙Delta Delta 梯度Multicalc"),
            {"sodium_mEq_l": 140, "chloride_mEq_l": 104, "bicarbonate_mEq_l": 12},
        )

        self.assertEqual(result.value, 24)
        self.assertIn("anion gap", result.interpretation)

    def test_anion_gap_delta_subtracts_baseline_gap(self):
        result = anion_gap_delta(
            metadata("阴离子间隙Delta Delta 梯度Multicalc"),
            {"anion_gap_mEq_l": 24, "baseline_anion_gap_mEq_l": 12},
        )

        self.assertEqual(result.value, 12)
        self.assertEqual(result.unit, "mEq/L")

    def test_male_urea_distribution_volume_watson(self):
        result = male_urea_distribution_volume_watson(
            metadata("分布容积"),
            {"age_years": 40, "height_cm": 175, "weight_kg": 70},
        )

        self.assertAlmostEqual(result.value, 40.9696, places=4)
        self.assertEqual(result.unit, "L")

    def test_female_urea_distribution_volume_watson(self):
        result = female_urea_distribution_volume_watson(
            metadata("分布容积"),
            {"height_cm": 165, "weight_kg": 60},
        )

        self.assertAlmostEqual(result.value, 30.3375, places=4)
        self.assertEqual(result.unit, "L")


if __name__ == "__main__":
    unittest.main()
