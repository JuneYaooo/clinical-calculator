"""Declared input contracts for built-in calculators."""

from __future__ import annotations

from functools import lru_cache
import json
import math
from pathlib import Path
from typing import Any

from clinical_calculators.models import InputSpec


CONTRACTS_DIR = Path(__file__).resolve().parent
_INPUT_FIELDS = {
    "name",
    "type",
    "unit",
    "required",
    "minimum",
    "maximum",
    "choices",
    "description",
    "item_text",
    "points",
    "optional",
    "default",
    "unit_alternatives",
}
_VALUE_TYPES = {"number", "boolean", "choice", "string", "sequence"}
_UNIT_OPERATIONS = {"multiply", "divide"}


class ContractError(ValueError):
    """Raised when a declared built-in input contract is invalid."""


def _reject_unknown(mapping: dict[str, Any], allowed: set[str], context: str) -> None:
    unknown = sorted(set(mapping) - allowed)
    if unknown:
        raise ContractError(f"{context} contains unknown fields: {', '.join(unknown)}")


def _finite_number(value: Any, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{context} must be numeric")
    converted = float(value)
    if not math.isfinite(converted):
        raise ContractError(f"{context} must be finite")
    return converted


def _optional_text(raw: dict[str, Any], key: str, context: str) -> str:
    value = raw.get(key, "")
    if not isinstance(value, str):
        raise ContractError(f"{context}.{key} must be a string")
    return value.strip()


def _parse_unit_alternatives(raw: Any, context: str) -> tuple[tuple[str, str, float], ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ContractError(f"{context}.unit_alternatives must be an array")
    parsed: list[tuple[str, str, float]] = []
    for index, item in enumerate(raw):
        item_context = f"{context}.unit_alternatives[{index}]"
        if not isinstance(item, list) or len(item) != 3:
            raise ContractError(f"{item_context} must be [unit, op, factor]")
        unit, operation, factor = item
        if not isinstance(unit, str) or not unit.strip():
            raise ContractError(f"{item_context} unit must be a non-empty string")
        if operation not in _UNIT_OPERATIONS:
            raise ContractError(
                f"{item_context} op must be multiply or divide"
            )
        parsed.append((unit.strip(), operation, _finite_number(factor, f"{item_context} factor")))
    return tuple(parsed)


def _parse_input(raw: Any, context: str) -> InputSpec:
    if not isinstance(raw, dict):
        raise ContractError(f"{context} must be an object")
    _reject_unknown(raw, _INPUT_FIELDS, context)

    name = raw.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ContractError(f"{context}.name must be a non-empty string")
    name = name.strip()
    if not name.isidentifier():
        raise ContractError(f"{context}.name must be a valid identifier")

    value_type = raw.get("type")
    if value_type not in _VALUE_TYPES:
        allowed = ", ".join(sorted(_VALUE_TYPES))
        raise ContractError(f"{context}.type must be one of: {allowed}")

    required = raw.get("required", True)
    optional = raw.get("optional", False)
    if not isinstance(required, bool):
        raise ContractError(f"{context}.required must be boolean")
    if not isinstance(optional, bool):
        raise ContractError(f"{context}.optional must be boolean")

    minimum = raw.get("minimum")
    maximum = raw.get("maximum")
    if minimum is not None:
        minimum = _finite_number(minimum, f"{context}.minimum")
    if maximum is not None:
        maximum = _finite_number(maximum, f"{context}.maximum")
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ContractError(f"{context} minimum cannot exceed maximum")

    choices_raw = raw.get("choices")
    choices: tuple[str, ...] = ()
    if choices_raw is not None:
        if (
            not isinstance(choices_raw, list)
            or len(choices_raw) < 2
            or not all(isinstance(item, str) and item.strip() for item in choices_raw)
        ):
            raise ContractError(f"{context}.choices must contain at least two non-empty strings")
        choices = tuple(item.strip() for item in choices_raw)
        if len(set(choices)) != len(choices):
            raise ContractError(f"{context}.choices must not contain duplicates")
    if value_type == "choice" and not choices:
        raise ContractError(f"{context}.choices is required for choice inputs")
    if value_type != "choice" and choices:
        raise ContractError(f"{context}.choices is only valid for choice inputs")

    points = raw.get("points")
    if points is not None:
        points = _finite_number(points, f"{context}.points")
        if value_type not in {"boolean", "number"}:
            raise ContractError(f"{context}.points is only valid for boolean or number inputs")

    return InputSpec(
        name=name,
        value_type=value_type,
        unit=_optional_text(raw, "unit", context),
        required=required,
        minimum=minimum,
        maximum=maximum,
        choices=choices,
        description=_optional_text(raw, "description", context),
        item_text=_optional_text(raw, "item_text", context),
        points=points,
        optional=optional,
        default=raw.get("default"),
        unit_alternatives=_parse_unit_alternatives(raw.get("unit_alternatives"), context),
    )


def _load_contract_directory(directory: Path) -> dict[str, tuple[InputSpec, ...]]:
    contracts: dict[str, tuple[InputSpec, ...]] = {}
    for path in sorted(directory.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ContractError(f"cannot parse contract file {path}: {exc}") from exc
        if not isinstance(raw, dict):
            raise ContractError(f"{path} root must be an object")
        for calculator_id, definition in raw.items():
            context = f"{path.name}:{calculator_id}"
            if not isinstance(calculator_id, str) or not calculator_id.strip():
                raise ContractError(f"{path.name} calculator IDs must be non-empty strings")
            if calculator_id in contracts:
                raise ContractError(f"duplicate declared contract ID: {calculator_id}")
            if not isinstance(definition, dict):
                raise ContractError(f"{context} must be an object")
            _reject_unknown(definition, {"inputs"}, context)
            inputs = definition.get("inputs")
            if not isinstance(inputs, list) or not inputs:
                raise ContractError(f"{context}.inputs must be a non-empty array")
            parsed = tuple(
                _parse_input(item, f"{context}.inputs[{index}]")
                for index, item in enumerate(inputs)
            )
            names = [item.name for item in parsed]
            if len(set(names)) != len(names):
                raise ContractError(f"{context}.inputs contains duplicate input names")
            contracts[calculator_id] = parsed
    return contracts


@lru_cache(maxsize=1)
def _load_default_contracts() -> dict[str, tuple[InputSpec, ...]]:
    return _load_contract_directory(CONTRACTS_DIR)


def load_declared_contracts(
    directory: str | Path | None = None,
) -> dict[str, tuple[InputSpec, ...]]:
    """Load all built-in contracts, or contracts from a test directory."""

    if directory is None:
        return _load_default_contracts()
    return _load_contract_directory(Path(directory))


def declared_contract_for(calculator_id: str) -> tuple[InputSpec, ...] | None:
    """Return the declared contract for one built-in calculator, when present."""

    return load_declared_contracts().get(calculator_id)


def validate_contract_alignment(
    contracts: dict[str, tuple[InputSpec, ...]],
    required_inputs_by_id: dict[str, tuple[str, ...]],
    registry_ids: set[str],
) -> None:
    """Reject orphaned contracts and input-name drift against implementations."""

    orphaned = sorted(set(contracts) - registry_ids)
    if orphaned:
        raise ContractError(
            "declared contract IDs are not present in the registry: " + ", ".join(orphaned)
        )
    for calculator_id, schema in contracts.items():
        if calculator_id not in required_inputs_by_id:
            raise ContractError(
                f"{calculator_id} has a declared contract but no executable implementation inputs"
            )
        declared = {spec.name for spec in schema}
        implemented = set(required_inputs_by_id[calculator_id])
        extra = sorted(declared - implemented)
        missing = sorted(implemented - declared)
        if extra or missing:
            details = []
            if extra:
                details.append("extra declared inputs: " + ", ".join(extra))
            if missing:
                details.append("missing declared inputs: " + ", ".join(missing))
            raise ContractError(f"{calculator_id} contract input mismatch; {'; '.join(details)}")


__all__ = [
    "CONTRACTS_DIR",
    "ContractError",
    "declared_contract_for",
    "load_declared_contracts",
    "validate_contract_alignment",
]
