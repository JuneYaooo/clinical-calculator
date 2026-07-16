import unittest

from clinical_calculators.calculators.common.hepatology_hcv_more import (
    apri_for_hepatitis_c_cirrhosis_probability,
    cirrhosis_discriminant_score_hepatitis_c,
    fib4_for_hepatitis_c_cirrhosis_probability,
    guci_for_hepatitis_c_cirrhosis_probability,
    lok_index_hepatitis_c_cirrhosis_probability,
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


class CommonHepatologyHcvMoreTest(unittest.TestCase):
    def test_lok_index_returns_logistic_probability(self):
        result = lok_index_hepatitis_c_cirrhosis_probability(
            metadata("丙型肝炎肝硬化的概率"),
            {"ast_u_l": 80, "alt_u_l": 60, "inr": 1.1, "platelets_10e9_l": 120},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 0.7004, places=4)
        self.assertEqual(result.unit, "probability")
        self.assertIn("likely", result.interpretation)

    def test_guci_uses_ast_uln_inr_and_platelets(self):
        result = guci_for_hepatitis_c_cirrhosis_probability(
            metadata("丙型肝炎肝硬化的概率"),
            {"ast_u_l": 80, "ast_uln_u_l": 40, "inr": 1.1, "platelets_10e9_l": 120},
        )

        self.assertAlmostEqual(result.value, 1.8333, places=4)
        self.assertIn("likely", result.interpretation)

    def test_apri_for_hcv_uses_standard_apri_formula(self):
        result = apri_for_hepatitis_c_cirrhosis_probability(
            metadata("丙型肝炎肝硬化的概率"),
            {"ast_u_l": 80, "ast_uln_u_l": 40, "platelets_10e9_l": 120},
        )

        self.assertAlmostEqual(result.value, 1.6667, places=4)
        self.assertIn("significant fibrosis likely", result.interpretation)

    def test_fib4_for_hcv_uses_age_ast_alt_platelets(self):
        result = fib4_for_hepatitis_c_cirrhosis_probability(
            metadata("丙型肝炎肝硬化的概率"),
            {"age_years": 55, "ast_u_l": 80, "alt_u_l": 60, "platelets_10e9_l": 120},
        )

        self.assertAlmostEqual(result.value, 4.7336, places=4)
        self.assertIn("likely", result.interpretation)

    def test_cds_scores_platelets_alt_ast_ratio_and_inr(self):
        result = cirrhosis_discriminant_score_hepatitis_c(
            metadata("丙型肝炎肝硬化的概率"),
            {"platelets_10e9_l": 120, "alt_u_l": 60, "ast_u_l": 80, "inr": 1.2},
        )

        self.assertEqual(result.status, "implemented")
        self.assertEqual(result.value["total_score"], 7)
        self.assertEqual(result.value["platelet_points"], 4)
        self.assertEqual(result.value["alt_ast_ratio_points"], 2)
        self.assertEqual(result.value["inr_points"], 1)
        self.assertEqual(result.unit, "points")
        self.assertIn("less likely", result.interpretation)


if __name__ == "__main__":
    unittest.main()
