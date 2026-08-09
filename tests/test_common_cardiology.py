import unittest

from clinical_calculators.calculators.common.cardiology import bazett_qtc
from clinical_calculators.models import CalculatorMetadata


def metadata(name_cn: str, name_en: str) -> CalculatorMetadata:
    return CalculatorMetadata(
        id=f"test-{name_en.lower().replace(' ', '-')}",
        category="common",
        subspecialty="cardiology",
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


class CommonCardiologyTest(unittest.TestCase):
    def test_bazett_qtc_calculates_corrected_qt_from_rr_seconds(self):
        result = bazett_qtc(
            metadata("QT间期校正 (EKG)", "QT Interval Correction (EKG)"),
            {"qt_seconds": 0.40, "rr_seconds": 1.0},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 0.40, places=4)
        self.assertEqual(result.unit, "seconds")

    def test_bazett_qtc_calculates_corrected_qt_from_heart_rate(self):
        result = bazett_qtc(
            metadata("QT间期校正 (EKG)", "QT Interval Correction (EKG)"),
            {"qt_seconds": 0.40, "heart_rate": 60},
        )

        self.assertEqual(result.status, "implemented")
        self.assertAlmostEqual(result.value, 0.40, places=4)
        self.assertEqual(result.unit, "seconds")

    def test_bazett_qtc_rejects_non_positive_heart_rate(self):
        with self.assertRaises(ValueError):
            bazett_qtc(
                metadata("QT间期校正 (EKG)", "QT Interval Correction (EKG)"),
                {"qt_seconds": 0.40, "heart_rate": 0},
            )

    def test_bazett_qtc_rejects_non_positive_rr_seconds(self):
        with self.assertRaises(ValueError):
            bazett_qtc(
                metadata("QT间期校正 (EKG)", "QT Interval Correction (EKG)"),
                {"qt_seconds": 0.40, "rr_seconds": 0},
            )

    def test_bazett_qtc_rejects_non_positive_qt_seconds(self):
        with self.assertRaises(ValueError):
            bazett_qtc(
                metadata("QT间期校正 (EKG)", "QT Interval Correction (EKG)"),
                {"qt_seconds": 0, "heart_rate": 60},
            )


if __name__ == "__main__":
    unittest.main()
