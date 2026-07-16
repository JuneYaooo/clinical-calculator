import math
import unittest

from clinical_calculators.calculators.common.respiratory_measurements_more import (
    closing_capacity,
    closing_capacity_to_total_lung_capacity_ratio,
    closing_volume_to_vital_capacity_ratio,
    estimated_pneumothorax_size,
    female_pediatric_predicted_fev1,
    female_pediatric_predicted_fvc,
    functional_residual_capacity,
    inspiratory_capacity,
    male_adjusted_predicted_fev1,
    male_adjusted_predicted_fvc,
    male_pediatric_predicted_fev1,
    male_pediatric_predicted_fvc,
    predicted_peak_expiratory_flow,
    rapid_shallow_breathing_index,
    residual_volume_to_total_lung_capacity_ratio,
    total_lung_capacity_from_volumes,
    vital_capacity,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str = "Respiratory measurement") -> CalculatorMetadata:
    return CalculatorMetadata(
        id=f"test-{name_cn}",
        category="common",
        subspecialty="respiratory",
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


class CommonRespiratoryMeasurementsMoreTest(unittest.TestCase):
    def test_female_pediatric_predicted_fev1_uses_age_and_height_meters(self):
        calculation = female_pediatric_predicted_fev1(
            metadata("女孩MultiCalc PFT预测值"),
            {"age_years": 10, "height_m": 1.3},
        )

        expected = math.exp(((1.5016 + (0.0119 * 10)) * 1.3) - 1.5974)
        self.assertAlmostEqual(calculation.value, expected, places=4)
        self.assertEqual(calculation.unit, "L")

    def test_female_pediatric_predicted_fvc_uses_age_and_height_meters(self):
        calculation = female_pediatric_predicted_fvc(
            metadata("女孩MultiCalc PFT预测值"),
            {"age_years": 10, "height_m": 1.3},
        )

        expected = math.exp(((1.48 + (0.0127 * 10)) * 1.3) - 1.4057)
        self.assertAlmostEqual(calculation.value, expected, places=4)
        self.assertEqual(calculation.unit, "L")

    def test_male_pediatric_predicted_fev1_uses_age_and_height_meters(self):
        calculation = male_pediatric_predicted_fev1(
            metadata("男孩MultiCalc PFT预测值"),
            {"age_years": 10, "height_m": 1.3},
        )

        expected = math.exp(((1.2669 + (0.0174 * 10)) * 1.3) - 1.2933)
        self.assertAlmostEqual(calculation.value, expected, places=4)
        self.assertEqual(calculation.unit, "L")

    def test_male_pediatric_predicted_fvc_uses_age_and_height_meters(self):
        calculation = male_pediatric_predicted_fvc(
            metadata("男孩MultiCalc PFT预测值"),
            {"age_years": 10, "height_m": 1.3},
        )

        expected = math.exp(((1.3731 + (0.0164 * 10)) * 1.3) - 1.2782)
        self.assertAlmostEqual(calculation.value, expected, places=4)
        self.assertEqual(calculation.unit, "L")

    def test_male_adjusted_predicted_pft_values_use_height_cm_age_and_race_factor(self):
        fev1 = male_adjusted_predicted_fev1(
            metadata("男性MultiCalc校正PFT"),
            {"height_cm": 175, "age_years": 40, "race_factor": 1.0},
        )
        fvc = male_adjusted_predicted_fvc(
            metadata("男性MultiCalc校正PFT"),
            {"height_cm": 175, "age_years": 40, "race_factor": 1.0},
        )

        self.assertAlmostEqual(fev1.value, 4.185, places=4)
        self.assertAlmostEqual(fvc.value, 5.1304, places=4)
        self.assertEqual(fev1.unit, "L")
        self.assertEqual(fvc.unit, "L")

    def test_predicted_peak_expiratory_flow_female_uses_age_and_height(self):
        calculation = predicted_peak_expiratory_flow(
            metadata("预计呼气峰流速-女性"),
            {"sex": "female", "age_years": 40, "height_cm": 165},
        )

        expected = math.exp((0.376 * math.log(40)) - (0.012 * 40) - (58.8 / 165) + 5.63)
        self.assertEqual(calculation.status, "implemented")
        self.assertAlmostEqual(calculation.value, expected, places=4)
        self.assertEqual(calculation.unit, "L/min")

    def test_predicted_peak_expiratory_flow_male_uses_age_and_height(self):
        calculation = predicted_peak_expiratory_flow(
            metadata("预计呼气峰流速-男性"),
            {"sex": "male", "age_years": 50, "height_cm": 180},
        )

        expected = math.exp((0.544 * math.log(50)) - (0.0151 * 50) - (74.7 / 180) + 5.48)
        self.assertAlmostEqual(calculation.value, expected, places=4)
        self.assertEqual(calculation.unit, "L/min")

    def test_predicted_peak_expiratory_flow_rejects_unknown_sex(self):
        with self.assertRaisesRegex(ValueError, "sex"):
            predicted_peak_expiratory_flow(
                metadata("预计呼气峰流速"),
                {"sex": "other", "age_years": 40, "height_cm": 165},
            )

    def test_rapid_shallow_breathing_index_uses_tidal_volume_liters(self):
        result = rapid_shallow_breathing_index(
            metadata("浅快呼吸指数", "Rapid Shallow Breathing Index"),
            {"respiratory_rate_bpm": 28, "tidal_volume_l": 0.35},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 80)
        self.assertEqual(result.unit, "breaths/min/L")
        self.assertIn("more favorable", result.interpretation)

    def test_rapid_shallow_breathing_index_accepts_tidal_volume_ml(self):
        result = rapid_shallow_breathing_index(
            metadata("浅快呼吸指数", "Rapid Shallow Breathing Index"),
            {"respiratory_rate_bpm": 36, "tidal_volume_ml": 300},
        )

        self.assertEqual(result.value, 120)
        self.assertIn("less favorable", result.interpretation)

    def test_estimated_pneumothorax_size_uses_cubed_diameter_ratio(self):
        calculation = estimated_pneumothorax_size(
            metadata("气胸大小估计"),
            {"lung_diameter_cm": 8, "hemithorax_diameter_cm": 10},
        )

        self.assertAlmostEqual(calculation.value, 48.8, places=4)
        self.assertEqual(calculation.unit, "%")

    def test_estimated_pneumothorax_size_rejects_lung_larger_than_hemithorax(self):
        with self.assertRaisesRegex(ValueError, "lung_diameter_cm"):
            estimated_pneumothorax_size(
                metadata("气胸大小估计"),
                {"lung_diameter_cm": 11, "hemithorax_diameter_cm": 10},
            )

    def test_residual_volume_to_total_lung_capacity_ratio_returns_percent(self):
        calculation = residual_volume_to_total_lung_capacity_ratio(
            metadata("残气量肺总量比"),
            {"residual_volume_l": 1.5, "total_lung_capacity_l": 6.0},
        )

        self.assertEqual(calculation.value, 25.0)
        self.assertEqual(calculation.unit, "%")

    def test_inspiratory_capacity_adds_inspiratory_reserve_and_tidal_volume(self):
        calculation = inspiratory_capacity(
            metadata("深吸气量"),
            {"inspiratory_reserve_volume_l": 3.0, "tidal_volume_l": 0.5},
        )

        self.assertEqual(calculation.value, 3.5)
        self.assertEqual(calculation.unit, "L")

    def test_vital_capacity_adds_inspiratory_tidal_and_expiratory_reserve_volumes(self):
        calculation = vital_capacity(
            metadata("肺活量"),
            {"inspiratory_reserve_volume_l": 3.0, "tidal_volume_l": 0.5, "expiratory_reserve_volume_l": 1.2},
        )

        self.assertEqual(calculation.value, 4.7)
        self.assertEqual(calculation.unit, "L")

    def test_total_lung_capacity_from_volumes_adds_four_component_volumes(self):
        calculation = total_lung_capacity_from_volumes(
            metadata("肺总量"),
            {
                "inspiratory_reserve_volume_l": 3.0,
                "tidal_volume_l": 0.5,
                "expiratory_reserve_volume_l": 1.2,
                "residual_volume_l": 1.3,
            },
        )

        self.assertEqual(calculation.value, 6.0)
        self.assertEqual(calculation.unit, "L")

    def test_functional_residual_capacity_adds_expiratory_reserve_and_residual_volume(self):
        calculation = functional_residual_capacity(
            metadata("功能残气量"),
            {"expiratory_reserve_volume_l": 1.2, "residual_volume_l": 1.3},
        )

        self.assertEqual(calculation.value, 2.5)
        self.assertEqual(calculation.unit, "L")

    def test_closing_capacity_adds_closing_volume_and_residual_volume(self):
        calculation = closing_capacity(
            metadata("闭合容量"),
            {"closing_volume_l": 0.8, "residual_volume_l": 1.3},
        )

        self.assertEqual(calculation.value, 2.1)
        self.assertEqual(calculation.unit, "L")

    def test_closing_volume_to_vital_capacity_ratio_returns_percent(self):
        calculation = closing_volume_to_vital_capacity_ratio(
            metadata("闭合气量肺活量比"),
            {"closing_volume_l": 0.8, "vital_capacity_l": 4.0},
        )

        self.assertEqual(calculation.value, 20.0)
        self.assertEqual(calculation.unit, "%")

    def test_closing_capacity_to_total_lung_capacity_ratio_returns_percent(self):
        calculation = closing_capacity_to_total_lung_capacity_ratio(
            metadata("闭合容量肺总量比"),
            {"closing_capacity_l": 2.1, "total_lung_capacity_l": 6.0},
        )

        self.assertEqual(calculation.value, 35.0)
        self.assertEqual(calculation.unit, "%")

    def test_ratio_denominators_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, "total_lung_capacity_l"):
            residual_volume_to_total_lung_capacity_ratio(
                metadata("残气量肺总量比"),
                {"residual_volume_l": 1.0, "total_lung_capacity_l": 0},
            )

    def test_volume_components_must_be_nonnegative(self):
        with self.assertRaisesRegex(ValueError, "tidal_volume_l"):
            inspiratory_capacity(
                metadata("深吸气量"),
                {"inspiratory_reserve_volume_l": 3.0, "tidal_volume_l": -0.1},
            )


if __name__ == "__main__":
    unittest.main()
