import re
import subprocess
import sys
from pathlib import Path

from clinical_calculators import load_registry


ROOT = Path(__file__).resolve().parents[1]
CATALOGS = (ROOT / "CALCULATORS.md", ROOT / "CALCULATORS_EN.md")


def catalog_ids(path: Path) -> list[str]:
    return re.findall(r"^\| (CALC-\d+) \|", path.read_text(encoding="utf-8"), re.MULTILINE)


def test_generated_calculator_catalogs_are_current():
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "generate_calculator_catalog.py"), "--check"],
        cwd=ROOT,
        check=True,
    )


def test_bilingual_catalogs_list_every_builtin_calculator_once():
    expected_ids = [skill.metadata.id for skill in load_registry(include_custom=False).skills]
    bilingual_ids = [catalog_ids(path) for path in CATALOGS]

    assert len(expected_ids) == 643
    assert len(set(expected_ids)) == 643
    for ids in bilingual_ids:
        assert len(ids) == len(expected_ids)
        assert len(set(ids)) == len(ids)
        assert set(ids) == set(expected_ids)
    assert bilingual_ids[0] == bilingual_ids[1]


def test_readmes_link_to_the_matching_language_catalog():
    assert "(./CALCULATORS.md)" in (ROOT / "README.md").read_text(encoding="utf-8")
    assert "(./CALCULATORS_EN.md)" in (ROOT / "README_EN.md").read_text(encoding="utf-8")


def test_english_catalog_does_not_include_chinese_name_column():
    english_catalog = (ROOT / "CALCULATORS_EN.md").read_text(encoding="utf-8")

    assert "| ID | Calculator | Implementation | Source |" in english_catalog
    assert "Chinese name" not in english_catalog
