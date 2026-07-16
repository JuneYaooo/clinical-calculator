import unittest

from clinical_calculators.calculators.common.emergency_rules_more import (
    canadian_ct_head_rule,
    mean_arterial_pressure,
    nexus_c_spine_rule,
    pediatric_endotracheal_tube_size,
    pao2_fio2_ratio_mods,
    shock_index,
    sirs_criteria,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str = "Emergency rule") -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="emergency",
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


class CommonEmergencyRulesMoreTest(unittest.TestCase):
    def test_pao2_fio2_ratio_accepts_fraction_and_identifies_moderate_ards(self):
        result = pao2_fio2_ratio_mods(
            metadata("PaO2 / FIO2 比值（MODS计算）"),
            {"pao2_mm_hg": 80, "fio2": 0.4},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 200)
        self.assertEqual(result.unit, "ratio")
        self.assertIn("moderate ARDS", result.interpretation)

    def test_pao2_fio2_ratio_accepts_percent_and_identifies_no_ards_threshold(self):
        result = pao2_fio2_ratio_mods(
            metadata("PaO2 / FIO2 比值（MODS计算）"),
            {"pao2_mm_hg": 160, "fio2": 40},
        )

        self.assertEqual(result.value, 400)
        self.assertEqual(result.unit, "ratio")
        self.assertIn("no ARDS oxygenation threshold", result.interpretation)

    def test_pao2_fio2_ratio_rejects_invalid_fio2(self):
        with self.assertRaises(ValueError):
            pao2_fio2_ratio_mods(
                metadata("PaO2 / FIO2 比值（MODS计算）"),
                {"pao2_mm_hg": 80, "fio2": 0},
            )

    def test_mean_arterial_pressure_uses_systolic_plus_twice_diastolic_over_three(self):
        result = mean_arterial_pressure(
            metadata("平均血管压力（体循环或肺循环）"),
            {"systolic_pressure_mm_hg": 120, "diastolic_pressure_mm_hg": 60},
        )

        self.assertEqual(result.value, 80)
        self.assertEqual(result.unit, "mm Hg")
        self.assertIn("mean vascular pressure", result.interpretation)

    def test_shock_index_elevated_at_point_nine(self):
        result = shock_index(
            metadata("休克指数"),
            {"heart_rate": 90, "systolic_bp": 100},
        )

        self.assertEqual(result.value, 0.9)
        self.assertEqual(result.unit, "")
        self.assertIn("elevated", result.interpretation)

    def test_shock_index_not_elevated_below_point_nine(self):
        result = shock_index(
            metadata("休克指数"),
            {"heart_rate": 80, "systolic_bp": 100},
        )

        self.assertEqual(result.value, 0.8)
        self.assertIn("not elevated", result.interpretation)

    def test_sirs_scores_temperature_hr_respiratory_and_wbc_criteria(self):
        result = sirs_criteria(
            metadata("SIRS标准"),
            {
                "temperature_c": 39,
                "heart_rate": 100,
                "respiratory_rate": 22,
                "paco2_mm_hg": 40,
                "wbc_10e9_l": 13,
                "bands_percent": 5,
            },
        )

        self.assertEqual(result.value, 4)
        self.assertEqual(result.unit, "points")
        self.assertIn("SIRS met", result.interpretation)

    def test_sirs_scores_respiratory_by_low_paco2_and_bands_by_percent(self):
        result = sirs_criteria(
            metadata("SIRS标准"),
            {
                "temperature_c": 37,
                "heart_rate": 80,
                "respiratory_rate": 18,
                "paco2_mm_hg": 31,
                "wbc_10e9_l": 8,
                "bands_percent": 11,
            },
        )

        self.assertEqual(result.value, 2)
        self.assertIn("SIRS met", result.interpretation)

    def test_sirs_one_criterion_does_not_meet_sirs(self):
        result = sirs_criteria(
            metadata("SIRS标准"),
            {
                "temperature_c": 35.9,
                "heart_rate": 90,
                "respiratory_rate": 20,
                "paco2_mm_hg": 32,
                "wbc_10e9_l": 4,
                "bands_percent": 10,
            },
        )

        self.assertEqual(result.value, 1)
        self.assertIn("SIRS not met", result.interpretation)

    def test_nexus_any_positive_criterion_indicates_imaging(self):
        result = nexus_c_spine_rule(
            metadata("NEXUS颈椎影像规则"),
            {
                "midline_cervical_tenderness": False,
                "focal_neurologic_deficit": True,
                "altered_level_of_alertness": False,
                "intoxication": False,
                "distracting_injury": True,
            },
        )

        self.assertEqual(result.value, 2)
        self.assertEqual(result.unit, "criteria")
        self.assertIn("imaging indicated", result.interpretation)

    def test_nexus_all_negative_is_low_risk(self):
        result = nexus_c_spine_rule(
            metadata("NEXUS颈椎影像规则"),
            {
                "midline_cervical_tenderness": False,
                "focal_neurologic_deficit": False,
                "altered_level_of_alertness": False,
                "intoxication": False,
                "distracting_injury": False,
            },
        )

        self.assertEqual(result.value, 0)
        self.assertIn("low risk", result.interpretation)

    def test_nexus_rejects_non_boolean_criterion(self):
        with self.assertRaises(ValueError):
            nexus_c_spine_rule(
                metadata("NEXUS颈椎影像规则"),
                {
                    "midline_cervical_tenderness": "yes",
                    "focal_neurologic_deficit": False,
                    "altered_level_of_alertness": False,
                    "intoxication": False,
                    "distracting_injury": False,
                },
            )

    def test_canadian_ct_head_rule_counts_high_and_medium_risk_criteria(self):
        result = canadian_ct_head_rule(
            metadata("加拿大头颅CT规则"),
            {
                "gcs_less_than_15_at_2_hours": True,
                "suspected_open_or_depressed_skull_fracture": False,
                "signs_basal_skull_fracture": True,
                "vomiting_two_or_more": False,
                "age_years": 65,
                "amnesia_before_impact_minutes": 30,
                "dangerous_mechanism": True,
            },
        )

        self.assertEqual(result.value, 5)
        self.assertEqual(result.unit, "criteria")
        self.assertIn("CT recommended", result.interpretation)

    def test_canadian_ct_head_rule_no_criteria_does_not_recommend_ct(self):
        result = canadian_ct_head_rule(
            metadata("加拿大头颅CT规则"),
            {
                "gcs_less_than_15_at_2_hours": False,
                "suspected_open_or_depressed_skull_fracture": False,
                "signs_basal_skull_fracture": False,
                "vomiting_two_or_more": False,
                "age_years": 64,
                "amnesia_before_impact_minutes": 29,
                "dangerous_mechanism": False,
            },
        )

        self.assertEqual(result.value, 0)
        self.assertIn("CT not recommended", result.interpretation)

    def test_pediatric_endotracheal_tube_size_uncuffed_age_four(self):
        result = pediatric_endotracheal_tube_size(
            metadata("儿童气管导管大小（1 到 8 周岁）"),
            {"age_years": 4, "cuffed": False},
        )

        self.assertEqual(result.value, 5)
        self.assertEqual(result.unit, "mm internal diameter")
        self.assertIn("uncuffed", result.interpretation)

    def test_pediatric_endotracheal_tube_size_cuffed_age_six(self):
        result = pediatric_endotracheal_tube_size(
            metadata("儿童气管导管大小（1 到 8 周岁）"),
            {"age_years": 6, "cuffed": True},
        )

        self.assertEqual(result.value, 5)
        self.assertIn("cuffed", result.interpretation)

    def test_pediatric_endotracheal_tube_size_requires_cuffed_key(self):
        with self.assertRaises(KeyError):
            pediatric_endotracheal_tube_size(
                metadata("儿童气管导管大小（1 到 8 周岁）"),
                {"age_years": 4},
            )

    def test_pediatric_endotracheal_tube_size_rejects_age_outside_one_to_eight(self):
        with self.assertRaises(ValueError):
            pediatric_endotracheal_tube_size(
                metadata("儿童气管导管大小（1 到 8 周岁）"),
                {"age_years": 9, "cuffed": False},
            )


if __name__ == "__main__":
    unittest.main()
