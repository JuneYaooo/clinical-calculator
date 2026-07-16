import unittest

from clinical_calculators.calculators.common.lipids_renal_simple import (
    friedewald_ldl_cholesterol,
    hemodialysis_percent_urea_reduction,
    urine_albumin_creatinine_ratio_category,
    urine_protein_excretion_estimate,
    vldl_cholesterol,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="lipids renal",
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


class CommonLipidsRenalSimpleTest(unittest.TestCase):
    def test_friedewald_ldl_cholesterol(self):
        result = friedewald_ldl_cholesterol(
            metadata("计算低密度脂蛋白胆固醇的Friedewald公式"),
            {"total_cholesterol_mg_dl": 200, "hdl_mg_dl": 50, "triglycerides_mg_dl": 150},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 120)
        self.assertEqual(result.unit, "mg/dL")

    def test_friedewald_ldl_rejects_triglycerides_400_or_higher(self):
        with self.assertRaisesRegex(ValueError, "triglycerides_mg_dl must be < 400"):
            friedewald_ldl_cholesterol(
                metadata("计算低密度脂蛋白胆固醇的Friedewald公式"),
                {"total_cholesterol_mg_dl": 200, "hdl_mg_dl": 50, "triglycerides_mg_dl": 400},
            )

    def test_vldl_cholesterol(self):
        result = vldl_cholesterol(
            metadata("极低密度脂蛋白（VLDL）"),
            {"triglycerides_mg_dl": 150},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 30)
        self.assertEqual(result.unit, "mg/dL")

    def test_urine_albumin_creatinine_ratio_categories(self):
        cases = [
            (10, "A1"),
            (100, "A2"),
            (400, "A3"),
        ]

        for ratio, category in cases:
            with self.subTest(ratio=ratio):
                result = urine_albumin_creatinine_ratio_category(
                    metadata("尿白蛋白肌酐比分类"),
                    {"albumin_mg_g_creatinine": ratio},
                )

                self.assertEqual(result.status, "implemented")
                self.assertAlmostEqual(result.value, ratio)
                self.assertEqual(result.unit, "mg/g")
                self.assertIn(category, result.interpretation)

    def test_urine_protein_excretion_estimate(self):
        result = urine_protein_excretion_estimate(
            metadata("尿蛋白排泄评估"),
            {"urine_protein_mg_dl": 100, "urine_volume_ml": 1500, "collection_hours": 24},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 1500)
        self.assertEqual(result.unit, "mg/day")

    def test_hemodialysis_percent_urea_reduction(self):
        result = hemodialysis_percent_urea_reduction(
            metadata("血液透析中尿素百分比的降低（PRU）"),
            {"pre_bun_mg_dl": 60, "post_bun_mg_dl": 18},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 70)
        self.assertEqual(result.unit, "%")


if __name__ == "__main__":
    unittest.main()
