import unittest

from clinical_calculators.calculators.common import function_lifestyle_scores
from clinical_calculators.calculators.common.function_lifestyle_scores import (
    barthel_activities_of_daily_living_index,
    berg_balance_scale,
    bone_mineral_density_t_score_interpretation,
    charlson_comorbidity_index,
    clinical_frailty_scale,
    community_periodontal_index,
    constant_murley_shoulder_score,
    decayed_missing_filled_teeth_index,
    fagerstrom_nicotine_dependence_test,
    foot_and_ankle_ability_measure,
    functional_ambulation_category,
    functional_independence_measure,
    gold_hypoglycemia_awareness_score,
    harris_hip_score,
    jaw_functional_limitation_scale,
    lower_extremity_functional_scale,
    lysholm_knee_score,
    kujala_anterior_knee_pain_scale,
    loe_silness_gingival_index,
    modified_dental_anxiety_scale,
    modified_rankin_scale,
    norton_pressure_ulcer_risk_scale,
    perceived_stress_scale_10,
    olerud_molander_ankle_score,
    quickdash_score,
    silness_loe_plaque_index,
    sarc_f_sarcopenia_screen,
    six_minute_walk_distance_predicted,
    tegner_activity_scale,
    tinetti_poma,
    timed_up_and_go_test,
    waist_to_height_ratio,
    waist_to_hip_ratio,
    visa_achilles_score,
    visa_patella_score,
    waterlow_pressure_ulcer_risk_score_prescored,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="function_lifestyle",
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


class CommonFunctionLifestyleScoresTest(unittest.TestCase):
    def test_clinical_frailty_scale_grade_seven_is_severely_frail(self):
        result = clinical_frailty_scale(
            metadata("临床衰弱量表", "Clinical Frailty Scale"),
            {"grade": 7},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 7)
        self.assertEqual(result.unit, "grade")
        self.assertIn("severe frailty", result.interpretation)

    def test_clinical_frailty_scale_rejects_grade_above_nine(self):
        with self.assertRaises(ValueError):
            clinical_frailty_scale(
                metadata("临床衰弱量表", "Clinical Frailty Scale"),
                {"grade": 10},
            )

    def test_alsfrs_r_sums_twelve_zero_to_four_function_scores(self):
        calculator = getattr(function_lifestyle_scores, "als_functional_rating_scale_revised", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("ALS功能评定修订量表", "ALS Functional Rating Scale-Revised"),
            {"items": [4, 4, 4, 4, 3, 3, 3, 2, 2, 1, 0, 0]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 30)
        self.assertEqual(result.unit, "points")
        self.assertIn("higher function", result.interpretation)

    def test_mg_adl_sums_eight_zero_to_three_symptom_scores(self):
        calculator = getattr(function_lifestyle_scores, "myasthenia_gravis_activities_of_daily_living", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("重症肌无力日常活动评分", "Myasthenia Gravis Activities of Daily Living"),
            {"items": [3, 2, 1, 0, 3, 2, 1, 0]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 12)
        self.assertEqual(result.unit, "points")
        self.assertIn("higher symptom burden", result.interpretation)

    def test_edmonton_frail_scale_classifies_twelve_as_severe_frailty(self):
        calculator = getattr(function_lifestyle_scores, "edmonton_frail_scale", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("埃德蒙顿衰弱量表", "Edmonton Frail Scale"),
            {"score": 12},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 12)
        self.assertEqual(result.unit, "points")
        self.assertIn("severe frailty", result.interpretation)

    def test_adverse_childhood_experiences_score_counts_ten_coded_exposures(self):
        calculator = getattr(function_lifestyle_scores, "adverse_childhood_experiences_score", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("ACE不良童年经历评分", "Adverse Childhood Experiences Score"),
            {"items": [True, False, True, True, False, False, True, False, False, False]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 4)
        self.assertEqual(result.unit, "count")
        self.assertIn("higher cumulative exposure", result.interpretation)

    def test_berg_balance_scale_sums_fourteen_zero_to_four_items(self):
        result = berg_balance_scale(
            metadata("Berg平衡量表", "Berg Balance Scale"),
            {"items": [4] * 13 + [3]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 55)
        self.assertEqual(result.unit, "points")
        self.assertIn("not below", result.interpretation)

    def test_berg_balance_scale_rejects_item_above_four(self):
        with self.assertRaises(ValueError):
            berg_balance_scale(
                metadata("Berg平衡量表", "Berg Balance Scale"),
                {"items": [4] * 13 + [5]},
            )

    def test_functional_ambulation_category_grade_five_is_independent(self):
        result = functional_ambulation_category(
            metadata("功能性步行分级", "Functional Ambulation Category"),
            {"grade": 5},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 5)
        self.assertEqual(result.unit, "category")
        self.assertIn("independent", result.interpretation)

    def test_functional_ambulation_category_rejects_grade_above_five(self):
        with self.assertRaises(ValueError):
            functional_ambulation_category(
                metadata("功能性步行分级", "Functional Ambulation Category"),
                {"grade": 6},
            )

    def test_timed_up_and_go_test_twelve_seconds_flags_fall_risk(self):
        result = timed_up_and_go_test(
            metadata("计时起立行走测试", "Timed Up and Go Test"),
            {"seconds": 12},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 12)
        self.assertEqual(result.unit, "seconds")
        self.assertIn("fall risk", result.interpretation)

    def test_timed_up_and_go_test_rejects_nonpositive_time(self):
        with self.assertRaises(ValueError):
            timed_up_and_go_test(
                metadata("计时起立行走测试", "Timed Up and Go Test"),
                {"seconds": 0},
            )

    def test_tinetti_poma_sums_balance_and_gait_components(self):
        result = tinetti_poma(
            metadata("Tinetti平衡与步态评估", "Tinetti POMA"),
            {"balance_score": 14, "gait_score": 10},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["total_score"], 24)
        self.assertEqual(result.value["balance_score"], 14)
        self.assertEqual(result.value["gait_score"], 10)
        self.assertEqual(result.unit, "points")
        self.assertIn("medium", result.interpretation)

    def test_tinetti_poma_rejects_gait_score_above_twelve(self):
        with self.assertRaises(ValueError):
            tinetti_poma(
                metadata("Tinetti平衡与步态评估", "Tinetti POMA"),
                {"balance_score": 16, "gait_score": 13},
            )

    def test_barthel_score_one_hundred_is_independent(self):
        result = barthel_activities_of_daily_living_index(
            metadata("Barthel日常生活活动指数", "Barthel Activities of Daily Living Index"),
            {
                "items": {
                    "feeding": 10,
                    "bathing": 5,
                    "grooming": 5,
                    "dressing": 10,
                    "bowels": 10,
                    "bladder": 10,
                    "toilet_use": 10,
                    "transfers": 15,
                    "mobility": 15,
                    "stairs": 10,
                }
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 100)
        self.assertEqual(result.unit, "points")
        self.assertIn("independent", result.interpretation)

    def test_barthel_score_sixty_is_severe_dependence(self):
        result = barthel_activities_of_daily_living_index(
            metadata("Barthel日常生活活动指数", "Barthel Activities of Daily Living Index"),
            {
                "items": {
                    "feeding": 10,
                    "bathing": 5,
                    "grooming": 5,
                    "dressing": 10,
                    "bowels": 5,
                    "bladder": 5,
                    "toilet_use": 10,
                    "transfers": 5,
                    "mobility": 5,
                    "stairs": 0,
                }
            },
        )

        self.assertEqual(result.value, 60)
        self.assertIn("severe dependence", result.interpretation)

    def test_barthel_rejects_nonstandard_item_value(self):
        items = {
            "feeding": 10,
            "bathing": 5,
            "grooming": 5,
            "dressing": 10,
            "bowels": 10,
            "bladder": 10,
            "toilet_use": 10,
            "transfers": 15,
            "mobility": 15,
            "stairs": 7,
        }

        with self.assertRaises(ValueError):
            barthel_activities_of_daily_living_index(
                metadata("Barthel日常生活活动指数", "Barthel Activities of Daily Living Index"),
                {"items": items},
            )

    def test_barthel_rejects_value_above_domain_maximum(self):
        items = {
            "feeding": 10,
            "bathing": 10,
            "grooming": 5,
            "dressing": 10,
            "bowels": 10,
            "bladder": 10,
            "toilet_use": 10,
            "transfers": 15,
            "mobility": 15,
            "stairs": 10,
        }

        with self.assertRaises(ValueError):
            barthel_activities_of_daily_living_index(
                metadata("Barthel日常生活活动指数", "Barthel Activities of Daily Living Index"),
                {"items": items},
            )

    def test_functional_independence_measure_sums_eighteen_one_to_seven_items(self):
        result = functional_independence_measure(
            metadata("功能独立性评定", "Functional Independence Measure"),
            {"items": [7] * 18},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 126)
        self.assertEqual(result.unit, "points")
        self.assertIn("higher independence", result.interpretation)

    def test_waterlow_prescored_components_sum_to_high_risk_category(self):
        result = waterlow_pressure_ulcer_risk_score_prescored(
            metadata("Waterlow压疮风险评分", "Waterlow Pressure Ulcer Risk Score"),
            {"component_points": [3, 2, 4, 3, 2, 1]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 15)
        self.assertEqual(result.unit, "points")
        self.assertIn("high risk", result.interpretation)

    def test_waterlow_prescored_components_reject_negative_points(self):
        with self.assertRaises(ValueError):
            waterlow_pressure_ulcer_risk_score_prescored(
                metadata("Waterlow压疮风险评分", "Waterlow Pressure Ulcer Risk Score"),
                {"component_points": [3, -1, 2]},
            )

    def test_bmd_t_score_classifies_osteoporosis_and_fragility_fracture(self):
        result = bone_mineral_density_t_score_interpretation(
            metadata("骨密度T值解读", "Bone Mineral Density T-score Interpretation"),
            {"t_score": -2.7, "fragility_fracture": True},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["classification"], "severe osteoporosis")
        self.assertIn("severe osteoporosis", result.interpretation)

    def test_community_periodontal_index_uses_highest_sextant_code(self):
        result = community_periodontal_index(
            metadata("社区牙周指数", "Community Periodontal Index"),
            {"sextant_codes": [0, 1, 2, 3, 4, 2]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 4)
        self.assertEqual(result.unit, "code")
        self.assertIn("pocket", result.interpretation)

    def test_modified_rankin_grade_three_returns_moderate_disability(self):
        result = modified_rankin_scale(
            metadata("改良Rankin量表", "Modified Rankin Scale"),
            {"grade": 3},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 3)
        self.assertEqual(result.unit, "grade")
        self.assertIn("moderate disability", result.interpretation)

    def test_modified_rankin_rejects_grade_outside_zero_to_six(self):
        with self.assertRaises(ValueError):
            modified_rankin_scale(
                metadata("改良Rankin量表", "Modified Rankin Scale"),
                {"grade": 7},
            )

    def test_sarc_f_score_four_is_risk_positive(self):
        result = sarc_f_sarcopenia_screen(
            metadata("SARC-F肌少症筛查", "SARC-F Sarcopenia Screen"),
            {"items": [1, 1, 1, 1, 0]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 4)
        self.assertEqual(result.unit, "points")
        self.assertIn("risk positive", result.interpretation)

    def test_sarc_f_rejects_wrong_item_count(self):
        with self.assertRaises(ValueError):
            sarc_f_sarcopenia_screen(
                metadata("SARC-F肌少症筛查", "SARC-F Sarcopenia Screen"),
                {"items": [0, 1, 2, 1]},
            )

    def test_perceived_stress_scale_10_score_twenty_seven_is_high(self):
        result = perceived_stress_scale_10(
            metadata("压力知觉量表10项", "Perceived Stress Scale-10"),
            {"items": [3, 3, 3, 3, 3, 3, 3, 2, 2, 2]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 27)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_perceived_stress_scale_10_rejects_item_over_four(self):
        with self.assertRaises(ValueError):
            perceived_stress_scale_10(
                metadata("压力知觉量表10项", "Perceived Stress Scale-10"),
                {"items": [0, 1, 2, 3, 4, 0, 1, 2, 3, 5]},
            )

    def test_fagerstrom_score_six_is_high_dependence(self):
        result = fagerstrom_nicotine_dependence_test(
            metadata("Fagerstrom尼古丁依赖测试", "Fagerstrom Test for Nicotine Dependence"),
            {"items": [3, 1, 1, 1, 0, 0]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 6)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_fagerstrom_rejects_total_above_ten(self):
        with self.assertRaises(ValueError):
            fagerstrom_nicotine_dependence_test(
                metadata("Fagerstrom尼古丁依赖测试", "Fagerstrom Test for Nicotine Dependence"),
                {"items": [3, 2, 2, 2, 2, 2]},
            )

    def test_gold_score_four_is_impaired_awareness(self):
        result = gold_hypoglycemia_awareness_score(
            metadata("Gold低血糖感知评分", "Gold Hypoglycemia Awareness Score"),
            {"score": 4},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 4)
        self.assertEqual(result.unit, "points")
        self.assertIn("impaired awareness", result.interpretation)

    def test_gold_rejects_score_below_one(self):
        with self.assertRaises(ValueError):
            gold_hypoglycemia_awareness_score(
                metadata("Gold低血糖感知评分", "Gold Hypoglycemia Awareness Score"),
                {"score": 0},
            )

    def test_six_minute_walk_distance_predicted_returns_predicted_and_percent(self):
        result = six_minute_walk_distance_predicted(
            metadata("6分钟步行距离预测值", "Six-Minute Walk Distance Predicted"),
            {"sex": "male", "age_years": 60, "height_cm": 175, "weight_kg": 80, "observed_6mwd_m": 450},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value["predicted_6mwd_m"], 573.75, places=2)
        self.assertAlmostEqual(result.value["percent_predicted"], 78.43, places=2)
        self.assertEqual(result.unit, "m")

    def test_charlson_comorbidity_index_adds_condition_and_age_weights(self):
        result = charlson_comorbidity_index(
            metadata("Charlson合并症指数", "Charlson Comorbidity Index"),
            {
                "age_years": 75,
                "myocardial_infarction": True,
                "congestive_heart_failure": False,
                "peripheral_vascular_disease": False,
                "cerebrovascular_disease": False,
                "dementia": False,
                "chronic_pulmonary_disease": False,
                "connective_tissue_disease": False,
                "peptic_ulcer_disease": False,
                "mild_liver_disease": False,
                "diabetes_without_end_organ_damage": True,
                "hemiplegia": False,
                "moderate_or_severe_renal_disease": True,
                "diabetes_with_end_organ_damage": False,
                "localized_solid_tumor": False,
                "leukemia": False,
                "lymphoma": False,
                "moderate_or_severe_liver_disease": False,
                "metastatic_solid_tumor": False,
                "aids": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["score"], 7)
        self.assertEqual(result.value["age_points"], 3)
        self.assertEqual(result.unit, "points")
        self.assertIn("higher comorbidity", result.interpretation)

    def test_waist_to_hip_ratio_uses_sex_specific_who_cutoffs(self):
        result = waist_to_hip_ratio(
            metadata("腰臀比", "Waist-to-Hip Ratio"),
            {"sex": "female", "waist_cm": 88, "hip_cm": 100},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 0.88)
        self.assertEqual(result.unit, "ratio")
        self.assertIn("increased", result.interpretation)

    def test_waist_to_height_ratio_uses_nice_thresholds(self):
        result = waist_to_height_ratio(
            metadata("腰高比", "Waist-to-Height Ratio"),
            {"waist_cm": 92, "height_cm": 170},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 0.5412, places=4)
        self.assertEqual(result.unit, "ratio")
        self.assertIn("increased", result.interpretation)

    def test_norton_pressure_ulcer_risk_scale_sums_five_one_to_four_components(self):
        result = norton_pressure_ulcer_risk_scale(
            metadata("Norton压疮风险评分", "Norton Scale"),
            {
                "physical_condition": 2,
                "mental_condition": 3,
                "activity": 2,
                "mobility": 2,
                "incontinence": 3,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 12)
        self.assertEqual(result.unit, "points")
        self.assertIn("risk", result.interpretation)

    def test_dmft_index_adds_decayed_missing_and_filled_teeth(self):
        result = decayed_missing_filled_teeth_index(
            metadata("龋失补指数", "Decayed, Missing, and Filled Teeth Index"),
            {"decayed_teeth": 2, "missing_teeth": 1, "filled_teeth": 3},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 6)
        self.assertEqual(result.unit, "teeth")

    def test_harris_hip_score_sums_pre_scored_components(self):
        result = harris_hip_score(
            metadata("Harris髋关节评分", "Harris Hip Score"),
            {"pain": 40, "function": 40, "absence_deformity": 4, "range_of_motion": 5},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 89)
        self.assertEqual(result.unit, "points")
        self.assertIn("good", result.interpretation)

    def test_harris_hip_score_rejects_component_above_domain_maximum(self):
        with self.assertRaises(ValueError):
            harris_hip_score(
                metadata("Harris髋关节评分", "Harris Hip Score"),
                {"pain": 45, "function": 40, "absence_deformity": 4, "range_of_motion": 5},
            )

    def test_harris_hip_score_allows_fractional_pre_scored_range_of_motion(self):
        result = harris_hip_score(
            metadata("Harris髋关节评分", "Harris Hip Score"),
            {"pain": 30, "function": 30, "absence_deformity": 4, "range_of_motion": 4.5},
        )

        self.assertEqual(result.value, 68.5)
        self.assertIn("poor", result.interpretation)

    def test_lysholm_knee_score_sums_pre_scored_components(self):
        result = lysholm_knee_score(
            metadata("Lysholm膝关节评分", "Lysholm Knee Score"),
            {
                "limp": 5,
                "support": 5,
                "locking": 15,
                "instability": 20,
                "pain": 25,
                "swelling": 10,
                "stair_climbing": 10,
                "squatting": 5,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 95)
        self.assertEqual(result.unit, "points")
        self.assertIn("top category", result.interpretation)

    def test_constant_murley_shoulder_score_sums_pre_scored_domains(self):
        result = constant_murley_shoulder_score(
            metadata("Constant-Murley肩关节评分", "Constant-Murley Shoulder Score"),
            {"pain": 12, "activities_of_daily_living": 18, "range_of_motion": 35, "strength": 20},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 85)
        self.assertEqual(result.unit, "points")
        self.assertIn("good", result.interpretation)

    def test_constant_murley_shoulder_score_allows_fractional_strength_points(self):
        result = constant_murley_shoulder_score(
            metadata("Constant-Murley肩关节评分", "Constant-Murley Shoulder Score"),
            {"pain": 10, "activities_of_daily_living": 15, "range_of_motion": 30, "strength": 12.5},
        )

        self.assertEqual(result.value, 67.5)
        self.assertIn("fair", result.interpretation)

    def test_lower_extremity_functional_scale_sums_twenty_zero_to_four_items(self):
        result = lower_extremity_functional_scale(
            metadata("下肢功能量表", "Lower Extremity Functional Scale"),
            {"items": [4] * 18 + [3, 2]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 77)
        self.assertEqual(result.unit, "points")
        self.assertIn("higher lower-extremity function", result.interpretation)

    def test_lower_extremity_functional_scale_rejects_wrong_item_count(self):
        with self.assertRaises(ValueError):
            lower_extremity_functional_scale(
                metadata("下肢功能量表", "Lower Extremity Functional Scale"),
                {"items": [4] * 19},
            )

    def test_dizziness_handicap_inventory_sums_twenty_five_coded_scores(self):
        calculator = getattr(function_lifestyle_scores, "dizziness_handicap_inventory", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("眩晕障碍量表", "Dizziness Handicap Inventory"),
            {"item_scores": [4] * 10 + [2] * 5 + [0] * 10},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 50)
        self.assertEqual(result.unit, "points")
        self.assertIn("greater perceived dizziness handicap", result.interpretation)

    def test_dizziness_handicap_inventory_rejects_non_dhi_item_score(self):
        calculator = getattr(function_lifestyle_scores, "dizziness_handicap_inventory", None)
        self.assertIsNotNone(calculator)

        with self.assertRaises(ValueError):
            calculator(
                metadata("眩晕障碍量表", "Dizziness Handicap Inventory"),
                {"item_scores": [4] * 24 + [1]},
            )

    def test_oxford_hip_score_sums_twelve_zero_to_four_item_scores(self):
        calculator = getattr(function_lifestyle_scores, "oxford_hip_score", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("Oxford髋关节评分", "Oxford Hip Score"),
            {"item_scores": [4] * 9 + [3, 2, 1]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 42)
        self.assertEqual(result.unit, "points")
        self.assertIn("better hip symptoms/function", result.interpretation)

    def test_oxford_hip_score_rejects_wrong_item_count(self):
        calculator = getattr(function_lifestyle_scores, "oxford_hip_score", None)
        self.assertIsNotNone(calculator)

        with self.assertRaises(ValueError):
            calculator(
                metadata("Oxford髋关节评分", "Oxford Hip Score"),
                {"item_scores": [4] * 11},
            )

    def test_oswestry_disability_index_scales_answered_sections_to_percent(self):
        calculator = getattr(function_lifestyle_scores, "oswestry_disability_index", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("Oswestry功能障碍指数", "Oswestry Disability Index"),
            {"section_scores": [2, 1, 4, 0, 3, 2, 1, 2, 1, None]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["raw_score"], 16)
        self.assertEqual(result.value["completed_sections"], 9)
        self.assertAlmostEqual(result.value["score_percent"], 35.5556, places=4)
        self.assertEqual(result.unit, "percent")

    def test_oswestry_disability_index_rejects_section_score_above_five(self):
        calculator = getattr(function_lifestyle_scores, "oswestry_disability_index", None)
        self.assertIsNotNone(calculator)

        with self.assertRaises(ValueError):
            calculator(
                metadata("Oswestry功能障碍指数", "Oswestry Disability Index"),
                {"section_scores": [0] * 9 + [6]},
            )

    def test_neck_disability_index_reports_raw_and_percent_scores(self):
        calculator = getattr(function_lifestyle_scores, "neck_disability_index", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("颈部功能障碍指数", "Neck Disability Index"),
            {"item_scores": [0, 1, 2, 3, 4, 5, 0, 1, 2, 3]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["raw_score"], 21)
        self.assertEqual(result.value["score_percent"], 42)
        self.assertEqual(result.unit, "points")
        self.assertIn("greater neck-related disability", result.interpretation)

    def test_neck_disability_index_rejects_missing_item_scores(self):
        calculator = getattr(function_lifestyle_scores, "neck_disability_index", None)
        self.assertIsNotNone(calculator)

        with self.assertRaises(ValueError):
            calculator(
                metadata("颈部功能障碍指数", "Neck Disability Index"),
                {"item_scores": [0] * 9 + [None]},
            )

    def test_quickdash_score_allows_one_missing_item_and_scales_to_zero_to_one_hundred(self):
        result = quickdash_score(
            metadata("QuickDASH上肢功能简表", "QuickDASH"),
            {"items": [2] * 10 + [None]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["completed_items"], 10)
        self.assertEqual(result.value["score"], 25)
        self.assertEqual(result.unit, "points")

    def test_dash_full_score_allows_three_missing_items_and_scales_to_zero_to_one_hundred(self):
        calculator = getattr(function_lifestyle_scores, "dash_full_score", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("DASH上肢功能评分", "DASH Full Score"),
            {"items": [3] * 27 + [None, None, None]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["completed_items"], 27)
        self.assertEqual(result.value["score"], 50)
        self.assertEqual(result.unit, "points")
        self.assertIn("greater disability", result.interpretation)

    def test_dash_full_score_requires_at_least_twenty_seven_completed_items(self):
        calculator = getattr(function_lifestyle_scores, "dash_full_score", None)
        self.assertIsNotNone(calculator)

        with self.assertRaises(ValueError):
            calculator(
                metadata("DASH上肢功能评分", "DASH Full Score"),
                {"items": [2] * 26 + [None, None, None, None]},
            )

    def test_tlics_sums_coded_components_and_recommends_operatve_at_five_or_more(self):
        calculator = getattr(function_lifestyle_scores, "thoracolumbar_injury_classification_severity_score", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata(
                "胸腰椎损伤分类和严重程度评分",
                "Thoracolumbar Injury Classification and Severity Scale",
            ),
            {"morphology": "burst", "posterior_ligamentous_complex": "injured", "neurologic_status": "intact"},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["total_score"], 5)
        self.assertEqual(result.value["morphology_points"], 2)
        self.assertEqual(result.value["posterior_ligamentous_complex_points"], 3)
        self.assertEqual(result.value["neurologic_status_points"], 0)
        self.assertEqual(result.unit, "points")
        self.assertIn("operative", result.interpretation)

    def test_tlics_score_four_is_either_nonoperative_or_operative(self):
        calculator = getattr(function_lifestyle_scores, "thoracolumbar_injury_classification_severity_score", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata(
                "胸腰椎损伤分类和严重程度评分",
                "Thoracolumbar Injury Classification and Severity Scale",
            ),
            {"morphology": "distraction", "posterior_ligamentous_complex": "intact", "neurologic_status": "intact"},
        )

        self.assertEqual(result.value["total_score"], 4)
        self.assertIn("nonoperative or operative", result.interpretation)

    def test_sins_sums_coded_components_and_classifies_unstable(self):
        calculator = getattr(function_lifestyle_scores, "spinal_instability_neoplastic_score", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("脊柱肿瘤不稳定评分", "Spinal Instability Neoplastic Score"),
            {
                "location": "junctional",
                "pain": "mechanical",
                "bone_lesion": "lytic",
                "alignment": "subluxation_translation",
                "vertebral_body_collapse": "greater_than_50_percent",
                "posterolateral_involvement": "bilateral",
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["total_score"], 18)
        self.assertEqual(result.value["location_points"], 3)
        self.assertEqual(result.value["pain_points"], 3)
        self.assertEqual(result.value["bone_lesion_points"], 2)
        self.assertEqual(result.value["alignment_points"], 4)
        self.assertEqual(result.value["vertebral_body_collapse_points"], 3)
        self.assertEqual(result.value["posterolateral_involvement_points"], 3)
        self.assertEqual(result.unit, "points")
        self.assertIn("unstable", result.interpretation)

    def test_sins_score_seven_is_potentially_unstable(self):
        calculator = getattr(function_lifestyle_scores, "spinal_instability_neoplastic_score", None)
        self.assertIsNotNone(calculator)

        result = calculator(
            metadata("脊柱肿瘤不稳定评分", "Spinal Instability Neoplastic Score"),
            {
                "location": "junctional",
                "pain": "mechanical",
                "bone_lesion": "blastic",
                "alignment": "normal",
                "vertebral_body_collapse": "none",
                "posterolateral_involvement": "unilateral",
            },
        )

        self.assertEqual(result.value["total_score"], 7)
        self.assertIn("potentially unstable", result.interpretation)

    def test_tegner_activity_scale_accepts_zero_to_ten_activity_grade(self):
        result = tegner_activity_scale(
            metadata("Tegner活动量表", "Tegner Activity Scale"),
            {"grade": 10},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 10)
        self.assertEqual(result.unit, "grade")
        self.assertIn("elite", result.interpretation)

    def test_olerud_molander_ankle_score_sums_prescored_domains(self):
        result = olerud_molander_ankle_score(
            metadata("Olerud-Molander踝关节评分", "Olerud-Molander Ankle Score"),
            {
                "pain": 25,
                "stiffness": 10,
                "swelling": 10,
                "stair_climbing": 10,
                "running": 5,
                "jumping": 5,
                "squatting": 5,
                "supports": 10,
                "work_activities": 20,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 100)
        self.assertEqual(result.unit, "points")
        self.assertIn("better ankle function", result.interpretation)

    def test_faam_reports_adl_and_sports_percent_scores(self):
        result = foot_and_ankle_ability_measure(
            metadata("足踝能力测量", "Foot and Ankle Ability Measure"),
            {"adl_items": [4] * 20 + [2], "sports_items": [3] * 8},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value["adl_percent"], 97.619, places=3)
        self.assertEqual(result.value["sports_percent"], 75)
        self.assertEqual(result.unit, "percent")

    def test_kujala_scale_sums_prescored_components_to_one_hundred(self):
        result = kujala_anterior_knee_pain_scale(
            metadata("Kujala髌股关节评分", "Kujala Anterior Knee Pain Scale"),
            {"component_points": [10] * 10},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 100)
        self.assertEqual(result.unit, "points")

    def test_visa_a_and_visa_p_scores_sum_eight_prescored_items(self):
        achilles = visa_achilles_score(
            metadata("VISA-A跟腱病评分", "Victorian Institute of Sport Assessment-Achilles"),
            {"items": [10] * 8},
        )
        patella = visa_patella_score(
            metadata("VISA-P髌腱病评分", "Victorian Institute of Sport Assessment-Patella"),
            {"items": [10] * 8},
        )

        self.assertEqual(achilles.status, "implemented")
        self.assertEqual(achilles.value, 80)
        self.assertEqual(patella.value, 80)
        self.assertIn("Achilles", achilles.interpretation)
        self.assertIn("patellar", patella.interpretation)

    def test_modified_dental_anxiety_scale_sums_five_one_to_five_items(self):
        result = modified_dental_anxiety_scale(
            metadata("改良牙科焦虑量表", "Modified Dental Anxiety Scale"),
            {"items": [5, 4, 4, 3, 3]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 19)
        self.assertEqual(result.unit, "points")
        self.assertIn("high dental anxiety", result.interpretation)

    def test_jaw_functional_limitation_scale_reports_total_and_mean_from_coded_items(self):
        result = jaw_functional_limitation_scale(
            metadata("颌功能受限量表", "Jaw Functional Limitation Scale"),
            {"items": [0, 1, 2, 3, 4, 5, 6, 7]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["total_score"], 28)
        self.assertEqual(result.value["mean_score"], 3.5)
        self.assertEqual(result.value["item_count"], 8)
        self.assertEqual(result.unit, "points")

    def test_jaw_functional_limitation_scale_accepts_twenty_item_form(self):
        result = jaw_functional_limitation_scale(
            metadata("颌功能受限量表", "Jaw Functional Limitation Scale"),
            {"items": [1] * 20},
        )

        self.assertEqual(result.value["total_score"], 20)
        self.assertEqual(result.value["mean_score"], 1)
        self.assertEqual(result.value["item_count"], 20)

    def test_silness_loe_plaque_index_averages_zero_to_three_surface_scores(self):
        result = silness_loe_plaque_index(
            metadata("Silness-Loe菌斑指数", "Silness-Loe Plaque Index"),
            {"surface_scores": [0, 1, 2, 3]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 1.5)
        self.assertEqual(result.unit, "index")

    def test_loe_silness_gingival_index_averages_zero_to_three_surface_scores(self):
        result = loe_silness_gingival_index(
            metadata("Loe-Silness牙龈指数", "Loe-Silness Gingival Index"),
            {"surface_scores": [0, 1, 2, 3]},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 1.5)
        self.assertEqual(result.unit, "index")
        self.assertIn("moderate", result.interpretation)


if __name__ == "__main__":
    unittest.main()
