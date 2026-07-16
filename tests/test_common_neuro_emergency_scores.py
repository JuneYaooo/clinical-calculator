import unittest

from clinical_calculators.calculators.common.neuro_emergency_scores import (
    abcd2_tia_risk,
    ich_score,
    perc_rule,
    san_francisco_syncope_rule,
    sudep_7_inventory_v2,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="neuro emergency",
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


class CommonNeuroEmergencyScoresTest(unittest.TestCase):
    def test_abcd2_scores_high_risk_tia(self):
        result = abcd2_tia_risk(
            metadata("ABCD2短暂性脑缺血发作风险", "ABCD2 TIA Risk"),
            {
                "age_years": 65,
                "systolic_bp": 150,
                "diastolic_bp": 80,
                "clinical_feature": "unilateral_weakness",
                "duration_minutes": 70,
                "diabetes": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 7)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_abcd2_rejects_unknown_clinical_feature(self):
        with self.assertRaises(ValueError):
            abcd2_tia_risk(
                metadata("ABCD2短暂性脑缺血发作风险", "ABCD2 TIA Risk"),
                {
                    "age_years": 55,
                    "systolic_bp": 120,
                    "diastolic_bp": 80,
                    "clinical_feature": "visual_symptoms",
                    "duration_minutes": 5,
                    "diabetes": 0,
                },
            )

    def test_ich_scores_all_high_risk_criteria(self):
        result = ich_score(
            metadata("ICH脑出血评分", "ICH Score"),
            {
                "gcs": 4,
                "age_years": 85,
                "ich_volume_ml": 40,
                "infratentorial_origin": True,
                "intraventricular_hemorrhage": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 6)
        self.assertEqual(result.unit, "points")
        self.assertIn("higher", result.interpretation)

    def test_perc_all_negative_is_perc_negative(self):
        result = perc_rule(
            metadata("PERC肺栓塞排除规则", "PERC Rule"),
            {
                "age_years": 30,
                "heart_rate": 80,
                "oxygen_saturation_percent": 99,
                "unilateral_leg_swelling": False,
                "hemoptysis": 0,
                "recent_surgery_or_trauma": False,
                "prior_dvt_pe": 0,
                "hormone_use": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 0)
        self.assertEqual(result.unit, "points")
        self.assertIn("PERC negative", result.interpretation)

    def test_perc_counts_positive_criteria(self):
        result = perc_rule(
            metadata("PERC肺栓塞排除规则", "PERC Rule"),
            {
                "age_years": 55,
                "heart_rate": 110,
                "oxygen_saturation_percent": 94,
                "unilateral_leg_swelling": False,
                "hemoptysis": True,
                "recent_surgery_or_trauma": False,
                "prior_dvt_pe": 0,
                "hormone_use": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 4)
        self.assertEqual(result.unit, "points")
        self.assertIn("positive", result.interpretation)

    def test_san_francisco_syncope_rule_all_negative_is_low_risk(self):
        result = san_francisco_syncope_rule(
            metadata("旧金山晕厥规则", "San Francisco Syncope Rule"),
            {
                "history_chf": False,
                "hematocrit_percent": 35,
                "abnormal_ecg": 0,
                "shortness_of_breath": False,
                "systolic_bp": 120,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 0)
        self.assertEqual(result.unit, "points")
        self.assertIn("low risk", result.interpretation)

    def test_san_francisco_syncope_rule_counts_high_risk_criteria(self):
        result = san_francisco_syncope_rule(
            metadata("旧金山晕厥规则", "San Francisco Syncope Rule"),
            {
                "history_chf": True,
                "hematocrit_percent": 29,
                "abnormal_ecg": 0,
                "shortness_of_breath": False,
                "systolic_bp": 80,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 3)
        self.assertEqual(result.unit, "points")
        self.assertIn("high risk", result.interpretation)

    def test_san_francisco_syncope_rule_rejects_non_boolean_flag(self):
        with self.assertRaises(ValueError):
            san_francisco_syncope_rule(
                metadata("旧金山晕厥规则", "San Francisco Syncope Rule"),
                {
                    "history_chf": "yes",
                    "hematocrit_percent": 35,
                    "abnormal_ecg": 0,
                    "shortness_of_breath": False,
                    "systolic_bp": 120,
                },
            )

    def test_sudep_7_reproduces_open_source_subject_scores(self):
        common = {
            "tonic_clonic_seizures_last_year": 4,
            "seizures_any_type_last_year": 4,
            "more_than_50_seizures_per_month": False,
            "duration_epilepsy_years": 20,
            "concurrent_antiseizure_medications": 3,
        }

        subject_1 = sudep_7_inventory_v2(
            metadata("SUDEP-7癫痫猝死风险", "SUDEP-7 Inventory"),
            {**common, "developmental_disability_or_iq_below_70": False},
        )
        subject_13 = sudep_7_inventory_v2(
            metadata("SUDEP-7癫痫猝死风险", "SUDEP-7 Inventory"),
            {**common, "developmental_disability_or_iq_below_70": True},
        )

        self.assertEqual(subject_1.value, 4)
        self.assertEqual(subject_13.value, 6)
        self.assertIn("not an individualized probability", subject_1.interpretation)

    def test_sudep_7_applies_mutually_exclusive_factors(self):
        calculation = sudep_7_inventory_v2(
            metadata("SUDEP-7癫痫猝死风险", "SUDEP-7 Inventory"),
            {
                "tonic_clonic_seizures_last_year": 10,
                "seizures_any_type_last_year": 1000,
                "more_than_50_seizures_per_month": True,
                "duration_epilepsy_years": 31,
                "concurrent_antiseizure_medications": 3,
                "developmental_disability_or_iq_below_70": True,
            },
        )

        self.assertEqual(calculation.value, 10)

    def test_sudep_7_preserves_strict_duration_and_seizure_boundaries(self):
        calculation = sudep_7_inventory_v2(
            metadata("SUDEP-7癫痫猝死风险", "SUDEP-7 Inventory"),
            {
                "tonic_clonic_seizures_last_year": 3,
                "seizures_any_type_last_year": 3,
                "more_than_50_seizures_per_month": False,
                "duration_epilepsy_years": 30,
                "concurrent_antiseizure_medications": 2,
                "developmental_disability_or_iq_below_70": False,
            },
        )

        self.assertEqual(calculation.value, 2)

    def test_sudep_7_rejects_negative_counts(self):
        with self.assertRaises(ValueError):
            sudep_7_inventory_v2(
                metadata("SUDEP-7癫痫猝死风险", "SUDEP-7 Inventory"),
                {
                    "tonic_clonic_seizures_last_year": -1,
                    "seizures_any_type_last_year": 0,
                    "more_than_50_seizures_per_month": False,
                    "duration_epilepsy_years": 1,
                    "concurrent_antiseizure_medications": 1,
                    "developmental_disability_or_iq_below_70": False,
                },
            )


if __name__ == "__main__":
    unittest.main()
