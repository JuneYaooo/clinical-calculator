import unittest

from clinical_calculators.calculators.common.egfr import (
    ckd_epi_2021_egfr_creatinine,
    mdrd_egfr,
    mdrd_egfr_si,
    urine_protein_creatinine_ratio,
)
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


class CommonEgfrTest(unittest.TestCase):
    def test_mdrd_male_nonblack_uses_conventional_creatinine(self):
        result = mdrd_egfr(
            metadata("MDRD公式估算肾小球滤过率"),
            {"age_years": 50, "serum_creatinine_mg_dl": 1.0, "sex": "male"},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 79.0947, places=4)
        self.assertEqual(result.unit, "mL/min/1.73m^2")
        self.assertIn("legacy MDRD", result.interpretation)

    def test_mdrd_female_nonblack_applies_sex_factor(self):
        result = mdrd_egfr(
            metadata("MDRD公式估算肾小球滤过率"),
            {"age_years": 50, "serum_creatinine_mg_dl": 1.0, "sex": "female"},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 58.6882, places=4)
        self.assertEqual(result.unit, "mL/min/1.73m^2")

    def test_mdrd_si_converts_creatinine_to_mg_dl(self):
        result = mdrd_egfr_si(
            metadata("由MDRD公式估算肾小球滤过率（采用国际单位）"),
            {"age_years": 50, "serum_creatinine_umol_l": 88.4, "sex": "male"},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 79.0947, places=4)
        self.assertEqual(result.unit, "mL/min/1.73m^2")

    def test_mdrd_accepts_boolean_like_black_flag(self):
        result = mdrd_egfr(
            metadata("MDRD公式估算肾小球滤过率"),
            {"age_years": 50, "serum_creatinine_mg_dl": 1.0, "sex": "male", "black": 1},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 95.8627, places=4)

    def test_mdrd_rejects_invalid_black_flag(self):
        with self.assertRaisesRegex(ValueError, "black must be bool or 0/1"):
            mdrd_egfr(
                metadata("MDRD公式估算肾小球滤过率"),
                {"age_years": 50, "serum_creatinine_mg_dl": 1.0, "sex": "male", "black": 2},
            )

    def test_2021_ckd_epi_female(self):
        result = ckd_epi_2021_egfr_creatinine(
            metadata("2021 CKD-EPI eGFR"),
            {"age_years": 50, "serum_creatinine_mg_dl": 1.0, "sex": "female"},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 68.6335, places=4)
        self.assertEqual(result.unit, "mL/min/1.73m^2")

    def test_2021_ckd_epi_male(self):
        result = ckd_epi_2021_egfr_creatinine(
            metadata("2021 CKD-EPI eGFR"),
            {"age_years": 50, "serum_creatinine_mg_dl": 1.0, "sex": "male"},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 91.6915, places=4)
        self.assertEqual(result.unit, "mL/min/1.73m^2")

    def test_egfr_rejects_unknown_sex(self):
        with self.assertRaisesRegex(ValueError, "sex must be 'male' or 'female'"):
            ckd_epi_2021_egfr_creatinine(
                metadata("2021 CKD-EPI eGFR"),
                {"age_years": 50, "serum_creatinine_mg_dl": 1.0, "sex": "unknown"},
            )

    def test_2021_ckd_epi_rejects_nonadult_age_and_zero_creatinine(self):
        with self.assertRaisesRegex(ValueError, "between 18 and 120"):
            ckd_epi_2021_egfr_creatinine(
                metadata("2021 CKD-EPI eGFR"),
                {"age_years": -10, "serum_creatinine_mg_dl": 1.0, "sex": "male"},
            )
        with self.assertRaisesRegex(ValueError, "serum_creatinine_mg_dl must be positive"):
            ckd_epi_2021_egfr_creatinine(
                metadata("2021 CKD-EPI eGFR"),
                {"age_years": 50, "serum_creatinine_mg_dl": 0, "sex": "male"},
            )

    def test_protein_creatinine_ratio_reports_mg_g(self):
        result = urine_protein_creatinine_ratio(
            metadata("蛋白肌酐比换算"),
            {"urine_protein_mg_dl": 20, "urine_creatinine_mg_dl": 100},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 200.0)
        self.assertEqual(result.unit, "mg/g")


if __name__ == "__main__":
    unittest.main()
