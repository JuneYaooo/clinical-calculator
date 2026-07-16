import unittest

from clinical_calculators.calculators.common.infection_allergy_more import (
    clostridioides_difficile_infection_severity,
    hypothermia_staging,
    lrinec_necrotizing_soft_tissue_infection_score,
    pen_fast_penicillin_allergy_score,
    predict_ie_score,
    tuberculin_skin_test_interpretation,
    thwaites_diagnostic_score,
    virsta_score,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="infection_allergy",
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


class CommonInfectionAllergyMoreTest(unittest.TestCase):
    def test_lrinec_high_risk_profile_scores_thirteen(self):
        result = lrinec_necrotizing_soft_tissue_infection_score(
            metadata("皮肤软组织感染坏死性筋膜炎风险", "LRINEC Score"),
            {
                "crp_mg_l": 200,
                "wbc_10e9_l": 30,
                "hemoglobin_g_dl": 10,
                "sodium_mEq_l": 130,
                "creatinine_mg_dl": 2.0,
                "glucose_mg_dl": 200,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 13)
        self.assertEqual(result.unit, "points")
        self.assertIn("high", result.interpretation)

    def test_lrinec_low_risk_profile_scores_zero(self):
        result = lrinec_necrotizing_soft_tissue_infection_score(
            metadata("皮肤软组织感染坏死性筋膜炎风险", "LRINEC Score"),
            {
                "crp_mg_l": 20,
                "wbc_10e9_l": 12,
                "hemoglobin_g_dl": 14,
                "sodium_mEq_l": 138,
                "creatinine_mg_dl": 1.0,
                "glucose_mg_dl": 100,
            },
        )

        self.assertEqual(result.value, 0)
        self.assertIn("low", result.interpretation)

    def test_pen_fast_score_below_three_is_low_risk(self):
        result = pen_fast_penicillin_allergy_score(
            metadata("PEN-FAST青霉素过敏评分", "PEN-FAST Score"),
            {
                "reaction_within_5_years": True,
                "anaphylaxis_or_angioedema": False,
                "severe_cutaneous_adverse_reaction": False,
                "treatment_required": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 2)
        self.assertEqual(result.unit, "points")
        self.assertIn("low risk", result.interpretation)

    def test_pen_fast_score_three_or_more_is_positive(self):
        result = pen_fast_penicillin_allergy_score(
            metadata("PEN-FAST青霉素过敏评分", "PEN-FAST Score"),
            {
                "reaction_within_5_years": True,
                "anaphylaxis_or_angioedema": True,
                "severe_cutaneous_adverse_reaction": False,
                "treatment_required": True,
            },
        )

        self.assertEqual(result.value, 5)
        self.assertIn("not low risk", result.interpretation)

    def test_tuberculin_skin_test_uses_selected_risk_threshold(self):
        result = tuberculin_skin_test_interpretation(
            metadata("结核感染TST解释", "Tuberculin Skin Test Interpretation"),
            {"induration_mm": 12, "risk_threshold_mm": 10},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["induration_mm"], 12)
        self.assertEqual(result.value["risk_threshold_mm"], 10)
        self.assertTrue(result.value["positive"])
        self.assertEqual(result.unit, "mm")
        self.assertIn("positive", result.interpretation)

    def test_tuberculin_skin_test_below_threshold_is_negative(self):
        result = tuberculin_skin_test_interpretation(
            metadata("结核感染TST解释", "Tuberculin Skin Test Interpretation"),
            {"induration_mm": 12, "risk_threshold_mm": 15},
        )

        self.assertFalse(result.value["positive"])
        self.assertIn("negative", result.interpretation)

    def test_c_difficile_severity_prioritizes_fulminant_features(self):
        result = clostridioides_difficile_infection_severity(
            metadata("Clostridioides difficile严重度分级", "C. difficile Infection Severity"),
            {
                "wbc_10e9_l": 9,
                "creatinine_mg_dl": 1.0,
                "hypotension_or_shock": False,
                "ileus": True,
                "megacolon": False,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, "fulminant")
        self.assertEqual(result.unit, "category")
        self.assertIn("fulminant", result.interpretation)

    def test_c_difficile_severity_uses_wbc_or_creatinine_for_severe(self):
        result = clostridioides_difficile_infection_severity(
            metadata("Clostridioides difficile严重度分级", "C. difficile Infection Severity"),
            {
                "wbc_10e9_l": 15,
                "creatinine_mg_dl": 1.0,
                "hypotension_or_shock": False,
                "ileus": False,
                "megacolon": False,
            },
        )

        self.assertEqual(result.value, "severe")
        self.assertIn("severe", result.interpretation)

    def test_c_difficile_severity_nonsevere_when_no_markers_present(self):
        result = clostridioides_difficile_infection_severity(
            metadata("Clostridioides difficile严重度分级", "C. difficile Infection Severity"),
            {
                "wbc_10e9_l": 12,
                "creatinine_mg_dl": 1.0,
                "hypotension_or_shock": False,
                "ileus": False,
                "megacolon": False,
            },
        )

        self.assertEqual(result.value, "non-severe")

    def test_hypothermia_staging_uses_swiss_clinical_stage_two(self):
        result = hypothermia_staging(
            metadata("低温症分期", "Hypothermia Staging"),
            {"mental_status": "impaired", "shivering": False, "vital_signs_present": True},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["stage"], "HT II")
        self.assertEqual(result.unit, "stage")
        self.assertIn("HT II", result.interpretation)

    def test_hypothermia_staging_no_vital_signs_is_stage_four(self):
        result = hypothermia_staging(
            metadata("低温症分期", "Hypothermia Staging"),
            {"mental_status": "unconscious", "shivering": False, "vital_signs_present": False},
        )

        self.assertEqual(result.value["stage"], "HT IV")

    def test_thwaites_bacterial_profile_scores_thirteen(self):
        result = thwaites_diagnostic_score(
            metadata("Thwaites结核性脑膜炎评分", "Thwaites Diagnostic Score"),
            {
                "age_years": 40,
                "illness_duration_days": 5,
                "blood_wbc_10e9_l": 16,
                "csf_wbc_cells_per_uL": 1000,
                "csf_neutrophils_percent": 80,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 13)
        self.assertEqual(result.unit, "points")
        self.assertIn("bacterial meningitis", result.interpretation)

    def test_thwaites_longer_illness_scores_minus_five_and_favors_tuberculous(self):
        result = thwaites_diagnostic_score(
            metadata("Thwaites结核性脑膜炎评分", "Thwaites Diagnostic Score"),
            {
                "age_years": 30,
                "illness_duration_days": 6,
                "blood_wbc_10e9_l": 10,
                "csf_wbc_cells_per_uL": 100,
                "csf_neutrophils_percent": 50,
            },
        )

        self.assertEqual(result.value, -5)
        self.assertIn("tuberculous meningitis", result.interpretation)

    def test_predict_ie_returns_day_one_and_day_five_scores(self):
        result = predict_ie_score(
            metadata("PREDICT心内膜炎风险", "PREDICT Score for Infective Endocarditis"),
            {
                "implantable_cardioverter_defibrillator": True,
                "permanent_pacemaker": True,
                "acquisition": "community",
                "positive_blood_culture_after_48h": True,
                "positive_blood_culture_after_72h": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["day1_score"], 7)
        self.assertEqual(result.value["day5_score"], 12)
        self.assertEqual(result.unit, "points")
        self.assertIn("day 5", result.interpretation)

    def test_predict_ie_healthcare_acquisition_scores_one_without_followup_culture_points(self):
        result = predict_ie_score(
            metadata("PREDICT心内膜炎风险", "PREDICT Score for Infective Endocarditis"),
            {
                "implantable_cardioverter_defibrillator": False,
                "permanent_pacemaker": False,
                "acquisition": "healthcare",
                "positive_blood_culture_after_48h": False,
                "positive_blood_culture_after_72h": False,
            },
        )

        self.assertEqual(result.value["day1_score"], 1)
        self.assertEqual(result.value["day5_score"], 1)
        self.assertIn("lower", result.interpretation)

    def test_virsta_maximum_profile_scores_thirty(self):
        result = virsta_score(
            metadata("VIRSTA金葡菌菌血症心内膜炎风险", "VIRSTA Score"),
            {
                "cerebral_or_peripheral_emboli": True,
                "meningitis": True,
                "permanent_intracardiac_device_or_previous_ie": True,
                "pre_existing_native_valve_disease": True,
                "intravenous_drug_use": True,
                "persistent_bacteremia_48h": True,
                "vertebral_osteomyelitis": True,
                "community_or_non_nosocomial_acquisition": True,
                "severe_sepsis_or_shock": True,
                "crp_greater_than_190_mg_l": True,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 30)
        self.assertEqual(result.unit, "points")
        self.assertIn("high risk", result.interpretation)

    def test_virsta_zero_to_two_is_low_risk(self):
        result = virsta_score(
            metadata("VIRSTA金葡菌菌血症心内膜炎风险", "VIRSTA Score"),
            {
                "cerebral_or_peripheral_emboli": False,
                "meningitis": False,
                "permanent_intracardiac_device_or_previous_ie": False,
                "pre_existing_native_valve_disease": False,
                "intravenous_drug_use": False,
                "persistent_bacteremia_48h": False,
                "vertebral_osteomyelitis": False,
                "community_or_non_nosocomial_acquisition": True,
                "severe_sepsis_or_shock": False,
                "crp_greater_than_190_mg_l": False,
            },
        )

        self.assertEqual(result.value, 2)
        self.assertIn("low risk", result.interpretation)


if __name__ == "__main__":
    unittest.main()
