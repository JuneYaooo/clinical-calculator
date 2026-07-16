import unittest

from clinical_calculators.calculators.common.more_scores_and_ratios import (
    clinical_dehydration_scale,
    four_coma_score,
    lams_los_angeles_motor_scale,
    ovarian_malignancy_risk_index,
    pediatric_percent_bmi95,
    sflt1_plgf_ratio,
    simplified_pesi_score,
    silverman_andersen_score,
    tof_ratio,
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


class CommonMoreScoresAndRatiosTest(unittest.TestCase):
    def test_silverman_andersen_score_sums_five_zero_to_two_components(self):
        result = silverman_andersen_score(
            metadata("Silverman-Andersen呼吸窘迫评分"),
            {
                "chest_abdominal_movement": 2,
                "intercostal_retractions": 1,
                "xiphoid_retractions": 2,
                "nasal_flaring": 1,
                "expiratory_grunt": 2,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 8)
        self.assertIn("severe", result.interpretation)

    def test_clinical_dehydration_scale_sums_four_zero_to_two_components(self):
        result = clinical_dehydration_scale(
            metadata("儿童脱水临床评分"),
            {"general_appearance": 1, "eyes": 1, "mucous_membranes": 1, "tears": 1},
        )

        self.assertEqual(result.value, 4)
        self.assertIn("mild/moderate", result.interpretation)

    def test_lams_score_uses_facial_arm_and_grip_points(self):
        result = lams_los_angeles_motor_scale(
            metadata("LAMS洛杉矶运动量表"), {"facial_droop": True, "arm_drift": 2, "grip_strength": 2}
        )

        self.assertEqual(result.value, 5)
        self.assertIn("higher", result.interpretation)

    def test_four_coma_score_sums_four_components(self):
        result = four_coma_score(
            metadata("FOUR昏迷评分"), {"eye": 4, "motor": 4, "brainstem": 4, "respiration": 4}
        )

        self.assertEqual(result.value, 16)
        self.assertIn("less impaired", result.interpretation)

    def test_ovarian_malignancy_risk_index_multiplies_u_m_and_ca125(self):
        result = ovarian_malignancy_risk_index(
            metadata("卵巢恶性肿瘤风险指数"), {"ultrasound_score": 3, "menopausal_score": 3, "ca125_u_ml": 100}
        )

        self.assertEqual(result.value, 900)
        self.assertIn("higher", result.interpretation)

    def test_sflt1_plgf_ratio(self):
        result = sflt1_plgf_ratio(metadata("sFlt-1/PlGF子痫前期风险比值"), {"sflt1_pg_ml": 1500, "plgf_pg_ml": 50})

        self.assertEqual(result.value, 30)
        self.assertEqual(result.unit, "ratio")

    def test_pediatric_percent_bmi95(self):
        result = pediatric_percent_bmi95(
            metadata("儿童肥胖严重度百分比BMI"), {"bmi": 32, "bmi_95th_percentile": 20}
        )

        self.assertEqual(result.value, 160)
        self.assertEqual(result.unit, "% of 95th percentile")
        self.assertIn("severe", result.interpretation)

    def test_simplified_pesi_score_counts_six_binary_criteria(self):
        result = simplified_pesi_score(
            metadata("简化PESI肺栓塞风险"),
            {
                "age_years": 81,
                "history_of_cancer": True,
                "chronic_cardiopulmonary_disease": False,
                "heart_rate": 111,
                "systolic_bp": 99,
                "oxygen_saturation_percent": 89,
            },
        )

        self.assertEqual(result.value, 5)
        self.assertIn("high", result.interpretation)

    def test_tof_ratio_divides_fourth_by_first_twitch(self):
        result = tof_ratio(metadata("四个成串比值"), {"t4_amplitude": 45, "t1_amplitude": 50})

        self.assertAlmostEqual(result.value, 0.9, places=4)
        self.assertIn("recovery", result.interpretation)


if __name__ == "__main__":
    unittest.main()
