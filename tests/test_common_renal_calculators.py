import unittest

from clinical_calculators.calculators.common.renal import (
    cockcroft_gault_creatinine_clearance,
    cockcroft_gault_creatinine_clearance_si,
    measured_creatinine_clearance,
    measured_creatinine_clearance_si,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str = "renal calculator") -> CalculatorMetadata:
    return CalculatorMetadata(
        id="TEST-RENAL",
        category="肾脏与泌尿生殖",
        subspecialty="",
        scenario="",
        name_cn=name_cn,
        name_en="Renal calculator",
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


class CommonRenalCalculatorsTest(unittest.TestCase):
    def test_cockcroft_gault_male_uses_creatinine_mg_dl(self):
        result = cockcroft_gault_creatinine_clearance(
            metadata("通过Cockcroft - Gault公式估算肌酐清除率"),
            {"age_years": 65, "weight_kg": 70, "serum_creatinine_mg_dl": 1.2, "sex": "male"},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 60.7639, places=4)
        self.assertEqual(result.unit, "mL/min")

    def test_cockcroft_gault_female_applies_085_factor(self):
        result = cockcroft_gault_creatinine_clearance(
            metadata("通过Cockcroft - Gault公式估算肌酐清除率"),
            {"age_years": 65, "weight_kg": 70, "serum_creatinine_mg_dl": 1.2, "sex": "female"},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 51.6493, places=4)
        self.assertEqual(result.unit, "mL/min")

    def test_cockcroft_gault_si_converts_creatinine_to_mg_dl(self):
        result = cockcroft_gault_creatinine_clearance_si(
            metadata("采用Cockcroft - Gault公式估算肌酐清除率（SI单位）"),
            {"age_years": 65, "weight_kg": 70, "serum_creatinine_umol_l": 106.08, "sex": "male"},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 60.7639, places=4)
        self.assertEqual(result.unit, "mL/min")

    def test_cockcroft_gault_rejects_unknown_sex(self):
        with self.assertRaisesRegex(ValueError, "sex must be 'male' or 'female'"):
            cockcroft_gault_creatinine_clearance(
                metadata("通过Cockcroft - Gault公式估算肌酐清除率"),
                {"age_years": 65, "weight_kg": 70, "serum_creatinine_mg_dl": 1.2, "sex": "unknown"},
            )

    def test_measured_creatinine_clearance_uses_standard_clearance_equation(self):
        result = measured_creatinine_clearance(
            metadata("肌酐清除率（测定）"),
            {
                "urine_creatinine_mg_dl": 100,
                "urine_volume_ml": 1440,
                "serum_creatinine_mg_dl": 1,
                "collection_minutes": 1440,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 100.0, places=4)
        self.assertEqual(result.unit, "mL/min")

    def test_measured_creatinine_clearance_si_converts_urine_creatinine(self):
        result = measured_creatinine_clearance_si(
            metadata("肌酐清除率（衡量SI单位）"),
            {
                "urine_creatinine_mmol_l": 10,
                "urine_volume_ml": 1440,
                "serum_creatinine_umol_l": 100,
                "collection_minutes": 1440,
            },
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 100.0, places=4)
        self.assertEqual(result.unit, "mL/min")


if __name__ == "__main__":
    unittest.main()
