from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys

import pytest

from clinical_calculators import InputSpec, load_registry
from clinical_calculators.contracts import (
    ContractError,
    load_declared_contracts,
    validate_contract_alignment,
)
from clinical_calculators.skill import CalculatorSkill


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "clinical_calculator.py"


def _write_contract(tmp_path: Path, input_definition: dict[str, object]) -> Path:
    path = tmp_path / "example.json"
    path.write_text(
        json.dumps({"CALC-TEST": {"inputs": [input_definition]}}),
        encoding="utf-8",
    )
    return path


def test_declared_contracts_match_registered_required_inputs():
    registry = load_registry(include_custom=False)
    contracts = load_declared_contracts()
    required_by_id = {
        skill.metadata.id: skill.required_inputs
        for skill in registry.runnable()
    }

    validate_contract_alignment(
        contracts,
        required_by_id,
        {skill.metadata.id for skill in registry.skills},
    )


def test_constructed_contract_input_mismatch_is_rejected():
    contracts = {
        "CALC-TEST": (
            InputSpec(name="declared_extra", value_type="number"),
        )
    }

    with pytest.raises(ContractError) as exc_info:
        validate_contract_alignment(
            contracts,
            {"CALC-TEST": ("implementation_input",)},
            {"CALC-TEST"},
        )

    message = str(exc_info.value)
    assert "CALC-TEST" in message
    assert "declared_extra" in message
    assert "implementation_input" in message


def test_orphaned_declared_contract_is_rejected():
    with pytest.raises(ContractError, match="CALC-ORPHAN"):
        validate_contract_alignment(
            {"CALC-ORPHAN": (InputSpec(name="value", value_type="number"),)},
            {},
            set(),
        )


def test_explicit_schema_has_priority_over_built_in_contract():
    metadata = load_registry(include_custom=False).get("CALC-0009").metadata
    explicit = (InputSpec(name="manifest_value", value_type="string"),)
    skill = CalculatorSkill(
        metadata,
        required_inputs=("manifest_value",),
        input_schema=explicit,
    )

    assert skill.input_schema is explicit


@pytest.mark.parametrize(
    ("input_definition", "message"),
    [
        ({"name": "value", "type": "number", "unknown": 1}, "unknown fields"),
        ({"name": "value", "type": "object"}, ".type must be one of"),
        (
            {"name": "value", "type": "number", "minimum": 2, "maximum": 1},
            "minimum cannot exceed maximum",
        ),
        ({"name": "value", "type": "choice", "choices": ["one"]}, "at least two"),
        ({"name": "value", "type": "string", "points": 1}, "points is only valid"),
    ],
)
def test_invalid_contract_fields_are_rejected(tmp_path, input_definition, message):
    _write_contract(tmp_path, input_definition)

    with pytest.raises(ContractError, match=message):
        load_declared_contracts(tmp_path)


def test_malformed_contract_json_is_rejected(tmp_path):
    (tmp_path / "broken.json").write_text("{", encoding="utf-8")

    with pytest.raises(ContractError, match="cannot parse contract file"):
        load_declared_contracts(tmp_path)


def test_input_spec_new_fields_are_optional_and_serializable():
    defaults = InputSpec(name="example", value_type="number")
    declared = InputSpec(
        name="example",
        value_type="number",
        item_text="来源原文",
        points=1,
        optional=True,
        default=0,
        unit_alternatives=(("alternative", "multiply", 2.0),),
    )

    assert defaults.item_text == ""
    assert defaults.points is None
    assert defaults.optional is False
    assert defaults.default is None
    assert defaults.unit_alternatives == ()
    assert asdict(declared)["unit_alternatives"] == (("alternative", "multiply", 2.0),)


def test_every_declared_input_has_a_concrete_type():
    registry = load_registry(include_custom=False)

    for calculator_id, contract in load_declared_contracts().items():
        info_inputs = [asdict(spec) for spec in registry.get(calculator_id).input_schema]
        assert len(info_inputs) == len(contract)
        assert all(item["value_type"] and item["value_type"] != "any" for item in info_inputs)


def test_cli_info_serializes_declared_contract_fields():
    completed = subprocess.run(
        [sys.executable, str(CLI), "info", "CALC-0009"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    assert [item["value_type"] for item in payload["required_inputs"]] == [
        "number",
        "number",
        "boolean",
    ]
    assert all(item["item_text"] for item in payload["required_inputs"])


@pytest.mark.parametrize(
    ("calculator_id", "inputs", "input_name"),
    [
        ("CALC-0001", {"eye": 5, "verbal": 5, "motor": 6}, "eye"),
        ("CALC-0006", {"age_years": 0, "cuffed": False}, "age_years"),
        (
            "CALC-0020",
            {
                "history": "wrong",
                "ecg": 0,
                "age_years": 45,
                "risk_factors_count": 0,
                "known_atherosclerotic_disease": False,
                "troponin_multiple_of_normal_limit": 1,
            },
            "history",
        ),
    ],
)
def test_declared_contract_rejects_upper_lower_and_wrong_type(
    calculator_id, inputs, input_name
):
    result = load_registry(include_custom=False).get(calculator_id).run(inputs)

    assert result.status == "invalid_inputs"
    assert input_name in result.message


def test_declared_boolean_rejects_true_string():
    result = load_registry(include_custom=False).get("CALC-0009").run(
        {
            "respiratory_rate": 22,
            "systolic_bp": 100,
            "altered_mentation": "true",
        }
    )

    assert result.status == "invalid_inputs"
    assert "altered_mentation" in result.message


def test_demo_contracts_do_not_declare_unverifiable_fixed_points():
    point_specs = [
        (calculator_id, spec)
        for calculator_id, schema in load_declared_contracts().items()
        for spec in schema
        if spec.points is not None
    ]

    assert point_specs == []
