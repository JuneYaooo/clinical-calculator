import json
from pathlib import Path

from clinical_calculators.contract_coverage import calculate_contract_coverage


ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "reports" / "contract_coverage_baseline.json"
RATCHET_MESSAGE = "契约覆盖不得倒退，如确为有意变更请同步更新基线文件"


def test_input_contract_coverage_does_not_regress():
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    current = calculate_contract_coverage()

    for key in (
        "calculators_without_declared_contract",
        "any_typed_inputs",
        "inputs_without_description",
    ):
        assert current[key] <= baseline[key], f"{RATCHET_MESSAGE}: {key}"
    assert (
        current["calculators_with_declared_contract"]
        >= baseline["calculators_with_declared_contract"]
    ), f"{RATCHET_MESSAGE}: calculators_with_declared_contract"
