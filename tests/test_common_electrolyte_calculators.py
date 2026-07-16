import unittest

from clinical_calculators.calculators.common.electrolytes import (
    corrected_calcium_hypoalbuminemia_si,
    effective_plasma_osmolality,
    estimated_serum_osmolality,
    osmolal_gap,
)
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=name_cn,
        category="common",
        subspecialty="electrolytes",
        scenario="unit test",
        name_cn=name_cn,
        name_en=name_cn,
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


class CommonElectrolyteCalculatorsTest(unittest.TestCase):
    def test_corrected_calcium_hypoalbuminemia_si(self):
        result = corrected_calcium_hypoalbuminemia_si(
            metadata("低白蛋白血症的校正钙（国际单位）"),
            {"calcium_mmol_l": 2.0, "albumin_g_l": 30},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 2.2)
        self.assertEqual(result.unit, "mmol/L")

    def test_estimated_serum_osmolality(self):
        result = estimated_serum_osmolality(
            metadata("渗透压估计（血清）"),
            {"sodium_mmol_l": 140, "glucose_mmol_l": 5, "bun_mmol_l": 5},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 290)
        self.assertEqual(result.unit, "mOsm/kg")

    def test_effective_plasma_osmolality(self):
        result = effective_plasma_osmolality(
            metadata("有效血浆渗透压"),
            {"sodium_mmol_l": 140, "glucose_mmol_l": 5},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 285)
        self.assertEqual(result.unit, "mOsm/kg")

    def test_osmolal_gap(self):
        result = osmolal_gap(
            metadata("渗透压间隙"),
            {"measured_osmolality_mosm_kg": 300, "estimated_osmolality_mosm_kg": 290},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 10)
        self.assertEqual(result.unit, "mOsm/kg")


if __name__ == "__main__":
    unittest.main()
