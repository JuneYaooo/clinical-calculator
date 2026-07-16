import unittest

from clinical_calculators.calculators.common.complex_rules_more import (
    adrenal_washout_percentages,
    kdigo_aki_stage,
    padua_nephrometry_score,
    renal_nephrometry_score,
    stone_nephrolithometry_score,
    stone_ureteral_stone_score,
    tips_risk_score,
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


class CommonComplexRulesMoreTest(unittest.TestCase):
    def test_stone_nephrolithometry_score_sums_five_components(self):
        result = stone_nephrolithometry_score(
            metadata("S.T.O.N.E.肾结石评分"),
            {
                "stone_area_mm2": 900,
                "skin_to_stone_distance_mm": 120,
                "obstruction": "severe",
                "calyces_involved": 3,
                "stone_density_hu": 1100,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 11)
        self.assertEqual(result.unit, "points")
        self.assertIn("high complexity", result.interpretation)

    def test_stone_nephrolithometry_score_low_complexity_boundaries(self):
        result = stone_nephrolithometry_score(
            metadata("S.T.O.N.E.肾结石评分"),
            {
                "stone_area_mm2": 399,
                "skin_to_stone_distance_mm": 99,
                "obstruction": "none",
                "calyces_involved": 1,
                "stone_density_hu": 949,
            },
        )

        self.assertEqual(result.value, 5)
        self.assertIn("low complexity", result.interpretation)

    def test_renal_nephrometry_score_sums_radius_exophytic_nearness_and_location(self):
        result = renal_nephrometry_score(
            metadata("R.E.N.A.L.肾肿瘤评分"),
            {
                "radius_cm": 7.2,
                "exophytic_percent": 0,
                "nearness_to_collecting_system_mm": 2,
                "location_relative_to_polar_lines": "entirely_between_polar_lines",
                "anterior_posterior": "posterior",
                "touches_main_renal_vessels": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 12)
        self.assertEqual(result.value["descriptor"], "12ph")
        self.assertEqual(result.unit, "points")
        self.assertIn("high complexity", result.interpretation)

    def test_renal_nephrometry_score_low_complexity_boundaries(self):
        result = renal_nephrometry_score(
            metadata("R.E.N.A.L.肾肿瘤评分"),
            {
                "radius_cm": 4.0,
                "exophytic_percent": 50,
                "nearness_to_collecting_system_mm": 7,
                "location_relative_to_polar_lines": "entirely_above_or_below_polar_lines",
                "anterior_posterior": "not_applicable",
            },
        )

        self.assertEqual(result.value["score"], 4)
        self.assertEqual(result.value["descriptor"], "4x")
        self.assertIn("low complexity", result.interpretation)

    def test_padua_nephrometry_score_sums_six_anatomic_features(self):
        result = padua_nephrometry_score(
            metadata("PADUA肾肿瘤评分"),
            {
                "longitudinal_location": "middle",
                "rim_location": "medial",
                "renal_sinus_involved": True,
                "collecting_system_involved": True,
                "tumor_size_cm": 7.1,
                "exophytic_percent": 20,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 13)
        self.assertEqual(result.unit, "points")
        self.assertIn("high risk", result.interpretation)

    def test_padua_nephrometry_score_low_risk_boundaries(self):
        result = padua_nephrometry_score(
            metadata("PADUA肾肿瘤评分"),
            {
                "longitudinal_location": "upper_or_lower",
                "rim_location": "lateral",
                "renal_sinus_involved": False,
                "collecting_system_involved": False,
                "tumor_size_cm": 4.0,
                "exophytic_percent": 50,
            },
        )

        self.assertEqual(result.value, 6)
        self.assertIn("low risk", result.interpretation)

    def test_padua_nephrometry_score_entirely_endophytic_scores_three_points(self):
        result = padua_nephrometry_score(
            metadata("PADUA肾肿瘤评分"),
            {
                "longitudinal_location": "middle",
                "rim_location": "medial",
                "renal_sinus_involved": True,
                "collecting_system_involved": True,
                "tumor_size_cm": 8,
                "exophytic_percent": 0,
            },
        )

        self.assertEqual(result.value, 14)
        self.assertIn("high risk", result.interpretation)

    def test_tips_risk_score_uses_creatinine_bilirubin_inr_and_etiology(self):
        result = tips_risk_score(
            metadata("TIPS风险预测/生存预测因素（经颈静脉肝内门体分流术）"),
            {"creatinine_mg_dl": 1.2, "bilirubin_mg_dl": 3, "inr": 1.5, "etiology_viral_or_other": True},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 1.6869, places=4)
        self.assertEqual(result.unit, "score")

    def test_adrenal_washout_returns_absolute_and_relative_percentages(self):
        result = adrenal_washout_percentages(
            metadata("肾上腺腺瘤洗脱率"),
            {"noncontrast_hu": 10, "enhanced_hu": 120, "delayed_hu": 50},
        )

        self.assertAlmostEqual(result.value["absolute_washout_percent"], 63.6364, places=4)
        self.assertAlmostEqual(result.value["relative_washout_percent"], 58.3333, places=4)
        self.assertIn("adenoma-compatible", result.interpretation)

    def test_stone_score_stratifies_high_probability(self):
        result = stone_ureteral_stone_score(
            metadata("STONE输尿管结石评分"),
            {
                "sex": "male",
                "pain_duration_hours": 4,
                "race": "white",
                "nausea_or_vomiting": "vomiting",
                "hematuria": True,
            },
        )

        self.assertEqual(result.value, 13)
        self.assertIn("high", result.interpretation)

    def test_kdigo_aki_stage_uses_worst_creatinine_or_urine_output_criterion(self):
        result = kdigo_aki_stage(
            metadata("KDIGO急性肾损伤分期"),
            {
                "baseline_creatinine_mg_dl": 1.0,
                "current_creatinine_mg_dl": 2.2,
                "creatinine_increase_mg_dl": 1.2,
                "urine_output_ml_kg_hr": 0.4,
                "urine_output_duration_hours": 14,
                "anuria_duration_hours": 0,
                "renal_replacement_therapy": False,
            },
        )

        self.assertEqual(result.value, 2)
        self.assertIn("stage 2", result.interpretation)

    def test_kdigo_aki_stage_returns_stage_3_for_renal_replacement_therapy(self):
        result = kdigo_aki_stage(
            metadata("KDIGO急性肾损伤分期"),
            {
                "baseline_creatinine_mg_dl": 1.0,
                "current_creatinine_mg_dl": 1.1,
                "creatinine_increase_mg_dl": 0.1,
                "urine_output_ml_kg_hr": 1.0,
                "urine_output_duration_hours": 0,
                "anuria_duration_hours": 0,
                "renal_replacement_therapy": True,
            },
        )

        self.assertEqual(result.value, 3)
        self.assertIn("stage 3", result.interpretation)


if __name__ == "__main__":
    unittest.main()
