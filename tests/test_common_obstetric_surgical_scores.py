import unittest

from clinical_calculators.calculators.common.obstetric_surgical_scores import (
    biophysical_profile_score,
    killip_acute_mi_heart_failure_classification,
    nyha_functional_classification,
    obstetric_shock_index,
    puqe_pregnancy_nausea_vomiting_score,
    surgical_apgar_score,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="obstetric_surgical",
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


class CommonObstetricSurgicalScoresTest(unittest.TestCase):
    def test_puqe_maximum_score_is_severe(self):
        result = puqe_pregnancy_nausea_vomiting_score(
            metadata("PUQE妊娠恶心呕吐评分", "PUQE Pregnancy Nausea and Vomiting Score"),
            {"nausea_hours_score": 5, "vomiting_score": 5, "retching_score": 5},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value, 15)
        self.assertEqual(result.unit, "points")
        self.assertIn("severe", result.interpretation)

    def test_puqe_minimum_score_is_mild(self):
        result = puqe_pregnancy_nausea_vomiting_score(
            metadata("PUQE妊娠恶心呕吐评分", "PUQE Pregnancy Nausea and Vomiting Score"),
            {"nausea_hours_score": 1, "vomiting_score": 1, "retching_score": 1},
        )

        self.assertEqual(result.value, 3)
        self.assertEqual(result.unit, "points")
        self.assertIn("mild", result.interpretation)

    def test_biophysical_profile_all_twos_is_reassuring(self):
        result = biophysical_profile_score(
            metadata("胎儿生物物理评分", "Biophysical Profile Score"),
            {
                "fetal_breathing": 2,
                "gross_body_movement": 2,
                "fetal_tone": 2,
                "amniotic_fluid": 2,
                "nonstress_test": 2,
            },
        )

        self.assertEqual(result.value, 10)
        self.assertEqual(result.unit, "points")
        self.assertIn("reassuring", result.interpretation)

    def test_biophysical_profile_all_zero_is_abnormal(self):
        result = biophysical_profile_score(
            metadata("胎儿生物物理评分", "Biophysical Profile Score"),
            {
                "fetal_breathing": 0,
                "gross_body_movement": 0,
                "fetal_tone": 0,
                "amniotic_fluid": 0,
                "nonstress_test": 0,
            },
        )

        self.assertEqual(result.value, 0)
        self.assertEqual(result.unit, "points")
        self.assertIn("abnormal", result.interpretation)

    def test_obstetric_shock_index_one_point_five_is_severe_concern(self):
        result = obstetric_shock_index(
            metadata("产后出血量/休克指数", "Obstetric Shock Index"),
            {"heart_rate": 120, "systolic_bp": 80},
        )

        self.assertEqual(result.value, 1.5)
        self.assertEqual(result.unit, "index")
        self.assertIn("severe concern", result.interpretation)

    def test_surgical_apgar_best_components_score_ten(self):
        result = surgical_apgar_score(
            metadata("手术Apgar评分", "Surgical Apgar Score"),
            {
                "estimated_blood_loss_ml": 50,
                "lowest_mean_arterial_pressure": 70,
                "lowest_heart_rate": 55,
            },
        )

        self.assertEqual(result.value, 10)
        self.assertEqual(result.unit, "points")
        self.assertIn("lower score", result.interpretation)

    def test_killip_class_three_is_pulmonary_edema(self):
        result = killip_acute_mi_heart_failure_classification(
            metadata("Killip急性心梗心衰分级", "Killip Classification"),
            {"class": 3},
        )

        self.assertEqual(result.value, 3)
        self.assertEqual(result.unit, "class")
        self.assertIn("pulmonary edema", result.interpretation)

    def test_nyha_class_four_has_symptoms_at_rest(self):
        result = nyha_functional_classification(
            metadata("NYHA心功能分级", "NYHA Functional Classification"),
            {"class": 4},
        )

        self.assertEqual(result.value, 4)
        self.assertEqual(result.unit, "class")
        self.assertIn("symptoms at rest", result.interpretation)


if __name__ == "__main__":
    unittest.main()
