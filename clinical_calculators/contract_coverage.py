"""Coverage metrics for built-in executable calculator input contracts."""

from __future__ import annotations

from .contracts import load_declared_contracts
from .registry import load_registry


def calculate_contract_coverage() -> dict[str, int]:
    """Measure declared-contract, type, and description coverage."""

    registry = load_registry(include_custom=False)
    executable = registry.runnable()
    declared_ids = set(load_declared_contracts())
    executable_ids = {skill.metadata.id for skill in executable}
    declared_executable_ids = declared_ids & executable_ids
    input_specs = [spec for skill in executable for spec in skill.input_schema]
    return {
        "executable_calculators": len(executable),
        "calculators_with_declared_contract": len(declared_executable_ids),
        "calculators_without_declared_contract": len(executable) - len(declared_executable_ids),
        "inputs_total": len(input_specs),
        "any_typed_inputs": sum(spec.value_type == "any" for spec in input_specs),
        "inputs_without_description": sum(not spec.description.strip() for spec in input_specs),
    }


__all__ = ["calculate_contract_coverage"]
