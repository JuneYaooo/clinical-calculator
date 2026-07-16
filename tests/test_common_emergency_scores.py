import unittest

from clinical_calculators.calculators.common.emergency_scores import (
    curb_65,
    glasgow_coma_scale,
    qsofa_score,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str = "emergency score") -> CalculatorMetadata:
    return CalculatorMetadata(
        id="TEST-EMERGENCY",
        category="common",
        subspecialty="",
        scenario="",
        name_cn=name_cn,
        name_en="Emergency score",
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


class CommonEmergencyScoresTest(unittest.TestCase):
    def test_glasgow_coma_scale_15_is_mild(self):
        result = glasgow_coma_scale(
            metadata("GLASGOW昏迷评分"),
            {"eye": 4, "verbal": 5, "motor": 6},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 15)
        self.assertEqual(result.unit, "points")
        self.assertIn("mild", result.interpretation)

    def test_glasgow_coma_scale_10_is_moderate(self):
        result = glasgow_coma_scale(
            metadata("GLASGOW昏迷评分"),
            {"eye": 2, "verbal": 3, "motor": 5},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 10)
        self.assertIn("moderate", result.interpretation)

    def test_qsofa_scores_three_risk_criteria(self):
        result = qsofa_score(
            metadata("序贯器官衰竭评估（快速）：qSOFA 评分"),
            {"respiratory_rate": 22, "systolic_bp": 90, "altered_mentation": True},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 3)
        self.assertEqual(result.unit, "points")
        self.assertIn("higher risk", result.interpretation)

    def test_curb_65_scores_all_five_criteria(self):
        result = curb_65(
            metadata("CURB-65肺炎严重度评分"),
            {
                "confusion": True,
                "urea_mmol_l": 8,
                "respiratory_rate": 30,
                "systolic_bp": 85,
                "diastolic_bp": 60,
                "age_years": 70,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 5)
        self.assertEqual(result.unit, "points")
        self.assertIn("severe", result.interpretation)

    def test_curb_65_scores_zero_for_low_risk_inputs(self):
        result = curb_65(
            metadata("肺炎严重度CURB-65"),
            {
                "confusion": 0,
                "urea_mmol_l": 7,
                "respiratory_rate": 29,
                "systolic_bp": 90,
                "diastolic_bp": 61,
                "age_years": 64,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 0)
        self.assertIn("low", result.interpretation)


if __name__ == "__main__":
    unittest.main()
