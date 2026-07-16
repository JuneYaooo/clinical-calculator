"""Safe declarative extension format for user-added formula calculators."""

from __future__ import annotations

import ast
from datetime import date
import json
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from .models import CalculationResult, CalculatorMetadata, InputSpec


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CUSTOM_DIR = ROOT / "custom_calculators"
CUSTOM_DIRS_ENV = "CLINICAL_CALCULATOR_CUSTOM_DIRS"
CUSTOM_ID_PATTERN = re.compile(r"^CUSTOM-[A-Z0-9][A-Z0-9-]{2,63}$")

_FUNCTIONS: dict[str, Callable[..., float]] = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
}
_BINARY_OPERATORS = {
    ast.Add: lambda left, right: left + right,
    ast.Sub: lambda left, right: left - right,
    ast.Mult: lambda left, right: left * right,
    ast.Div: lambda left, right: left / right,
    ast.Mod: lambda left, right: left % right,
    ast.Pow: lambda left, right: left**right,
}
_COMPARATORS = {
    ast.Eq: lambda left, right: left == right,
    ast.NotEq: lambda left, right: left != right,
    ast.Lt: lambda left, right: left < right,
    ast.LtE: lambda left, right: left <= right,
    ast.Gt: lambda left, right: left > right,
    ast.GtE: lambda left, right: left >= right,
}


class ManifestError(ValueError):
    """Raised when a custom calculator manifest is unsafe or incomplete."""


class SafeExpression:
    def __init__(self, expression: str, allowed_names: set[str]) -> None:
        self.expression = expression.strip()
        if not self.expression:
            raise ManifestError("formula expression cannot be empty")
        try:
            self.tree = ast.parse(self.expression, mode="eval")
        except SyntaxError as exc:
            raise ManifestError(f"invalid expression syntax: {exc.msg}") from exc
        if sum(1 for _ in ast.walk(self.tree)) > 120:
            raise ManifestError("expression is too complex")
        self.allowed_names = allowed_names
        self._validate(self.tree)

    def _validate(self, node: ast.AST) -> None:
        if isinstance(node, ast.Expression):
            self._validate(node.body)
        elif isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float, str, bool)):
                raise ManifestError("only numeric, string, and boolean constants are allowed")
        elif isinstance(node, ast.Name):
            if node.id not in self.allowed_names and node.id not in _FUNCTIONS:
                raise ManifestError(f"unknown expression name: {node.id}")
        elif isinstance(node, ast.BinOp):
            if type(node.op) not in _BINARY_OPERATORS:
                raise ManifestError(f"operator {type(node.op).__name__} is not allowed")
            if isinstance(node.op, ast.Pow) and isinstance(node.right, ast.Constant):
                if not isinstance(node.right.value, (int, float)) or abs(node.right.value) > 100:
                    raise ManifestError("constant exponents must be between -100 and 100")
            self._validate(node.left)
            self._validate(node.right)
        elif isinstance(node, ast.UnaryOp):
            if not isinstance(node.op, (ast.UAdd, ast.USub, ast.Not)):
                raise ManifestError(f"unary operator {type(node.op).__name__} is not allowed")
            self._validate(node.operand)
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCTIONS:
                raise ManifestError("only allowlisted math functions may be called")
            if node.keywords:
                raise ManifestError("keyword arguments are not allowed in expressions")
            for argument in node.args:
                self._validate(argument)
        elif isinstance(node, ast.Compare):
            self._validate(node.left)
            for operator in node.ops:
                if type(operator) not in _COMPARATORS:
                    raise ManifestError(f"comparison {type(operator).__name__} is not allowed")
            for comparator in node.comparators:
                self._validate(comparator)
        elif isinstance(node, ast.BoolOp):
            if not isinstance(node.op, (ast.And, ast.Or)):
                raise ManifestError("unsupported boolean operator")
            for value in node.values:
                self._validate(value)
        elif isinstance(node, ast.IfExp):
            self._validate(node.test)
            self._validate(node.body)
            self._validate(node.orelse)
        else:
            raise ManifestError(f"expression element {type(node).__name__} is not allowed")

    def evaluate(self, values: dict[str, Any]) -> Any:
        return self._evaluate(self.tree.body, values)

    def _evaluate(self, node: ast.AST, values: dict[str, Any]) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in _FUNCTIONS:
                return _FUNCTIONS[node.id]
            return values[node.id]
        if isinstance(node, ast.BinOp):
            return _BINARY_OPERATORS[type(node.op)](
                self._evaluate(node.left, values), self._evaluate(node.right, values)
            )
        if isinstance(node, ast.UnaryOp):
            operand = self._evaluate(node.operand, values)
            if isinstance(node.op, ast.UAdd):
                return +operand
            if isinstance(node.op, ast.USub):
                return -operand
            return not operand
        if isinstance(node, ast.Call):
            function = _FUNCTIONS[node.func.id]
            return function(*(self._evaluate(argument, values) for argument in node.args))
        if isinstance(node, ast.Compare):
            left = self._evaluate(node.left, values)
            for operator, comparator in zip(node.ops, node.comparators):
                right = self._evaluate(comparator, values)
                if not _COMPARATORS[type(operator)](left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return all(self._evaluate(value, values) for value in node.values)
            return any(self._evaluate(value, values) for value in node.values)
        if isinstance(node, ast.IfExp):
            branch = node.body if self._evaluate(node.test, values) else node.orelse
            return self._evaluate(branch, values)
        raise ManifestError(f"cannot evaluate {type(node).__name__}")


@dataclass(frozen=True)
class CustomCalculatorDefinition:
    metadata: CalculatorMetadata
    implementation: Callable[[CalculatorMetadata, dict[str, Any]], CalculationResult]
    required_inputs: tuple[str, ...]
    input_schema: tuple[InputSpec, ...]
    manifest_path: Path


def _reject_unknown(mapping: dict[str, Any], allowed: set[str], context: str) -> None:
    unknown = sorted(set(mapping) - allowed)
    if unknown:
        raise ManifestError(f"{context} contains unknown fields: {', '.join(unknown)}")


def _required_string(mapping: dict[str, Any], key: str, context: str = "manifest") -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{context}.{key} must be a non-empty string")
    return value.strip()


def _validate_input_definition(raw: Any, index: int) -> tuple[InputSpec, dict[str, Any]]:
    if not isinstance(raw, dict):
        raise ManifestError(f"inputs[{index}] must be an object")
    _reject_unknown(
        raw,
        {
            "name",
            "type",
            "unit",
            "minimum",
            "maximum",
            "exclusive_minimum",
            "exclusive_maximum",
            "choices",
            "description",
        },
        f"inputs[{index}]",
    )
    name = _required_string(raw, "name", f"inputs[{index}]")
    if not name.isidentifier():
        raise ManifestError(f"inputs[{index}].name must be a valid identifier")
    if name in _FUNCTIONS or name == "value":
        raise ManifestError(f"inputs[{index}].name is reserved: {name}")
    value_type = raw.get("type", "number")
    if value_type not in {"number", "boolean", "choice"}:
        raise ManifestError(f"inputs[{index}].type must be number, boolean, or choice")
    choices = raw.get("choices", [])
    if value_type == "choice":
        if (
            not isinstance(choices, list)
            or len(choices) < 2
            or not all(isinstance(x, str) and x.strip() for x in choices)
            or len(set(choices)) != len(choices)
        ):
            raise ManifestError(f"inputs[{index}].choices must contain at least two strings")
    elif choices:
        raise ManifestError(f"inputs[{index}].choices is only valid for choice inputs")
    minimum = raw.get("minimum")
    maximum = raw.get("maximum")
    for label, value in (("minimum", minimum), ("maximum", maximum)):
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
            raise ManifestError(f"inputs[{index}].{label} must be numeric")
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ManifestError(f"inputs[{index}] minimum cannot exceed maximum")
    for flag in ("exclusive_minimum", "exclusive_maximum"):
        if flag in raw and not isinstance(raw[flag], bool):
            raise ManifestError(f"inputs[{index}].{flag} must be boolean")
    if minimum == maximum and (
        raw.get("exclusive_minimum", False) or raw.get("exclusive_maximum", False)
    ):
        raise ManifestError(f"inputs[{index}] exclusive bounds leave no valid value")
    unit = str(raw.get("unit", "")).strip()
    if value_type == "number" and not unit:
        raise ManifestError(f"inputs[{index}].unit is required for numbers; use '1' if dimensionless")
    spec = InputSpec(
        name=name,
        value_type=value_type,
        unit=unit,
        minimum=float(minimum) if minimum is not None else None,
        maximum=float(maximum) if maximum is not None else None,
        choices=tuple(choices),
        description=str(raw.get("description", "")).strip(),
    )
    return spec, raw


def _validate_runtime_input(spec: InputSpec, raw: dict[str, Any], value: Any) -> Any:
    if spec.value_type == "number":
        if isinstance(value, bool):
            raise ValueError(f"{spec.name} must be numeric")
        try:
            converted = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{spec.name} must be numeric") from exc
        if not math.isfinite(converted):
            raise ValueError(f"{spec.name} must be finite")
        if spec.minimum is not None:
            if raw.get("exclusive_minimum", False) and converted <= spec.minimum:
                raise ValueError(f"{spec.name} must be greater than {spec.minimum:g}")
            if not raw.get("exclusive_minimum", False) and converted < spec.minimum:
                raise ValueError(f"{spec.name} must be at least {spec.minimum:g}")
        if spec.maximum is not None:
            if raw.get("exclusive_maximum", False) and converted >= spec.maximum:
                raise ValueError(f"{spec.name} must be less than {spec.maximum:g}")
            if not raw.get("exclusive_maximum", False) and converted > spec.maximum:
                raise ValueError(f"{spec.name} must be at most {spec.maximum:g}")
        return converted
    if spec.value_type == "boolean":
        if isinstance(value, bool):
            return value
        if value in (0, 1):
            return bool(value)
        raise ValueError(f"{spec.name} must be a boolean or 0/1")
    converted = str(value).strip()
    if converted not in spec.choices:
        raise ValueError(f"{spec.name} must be one of: {', '.join(spec.choices)}")
    return converted


def _finite_number(value: Any, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ManifestError(f"{context} must be numeric")
    converted = float(value)
    if not math.isfinite(converted):
        raise ManifestError(f"{context} must be finite")
    return converted


def _validate_outputs(
    raw: dict[str, Any], schema_version: int
) -> tuple[tuple[tuple[str, str, int], ...], bool, str]:
    output = raw.get("output")
    outputs = raw.get("outputs")
    if schema_version == 1 and outputs is not None:
        raise ManifestError("schema_version 1 does not support outputs")
    if (output is None) == (outputs is None):
        raise ManifestError("provide exactly one of output or outputs")
    if output is not None:
        if not isinstance(output, dict):
            raise ManifestError("output must be an object")
        _reject_unknown(output, {"unit", "round"}, "output")
        unit = _required_string(output, "unit", "output")
        digits = output.get("round", 4)
        if isinstance(digits, bool) or not isinstance(digits, int) or not 0 <= digits <= 10:
            raise ManifestError("output.round must be an integer from 0 to 10")
        return (("value", unit, digits),), False, unit

    if not isinstance(outputs, list) or len(outputs) < 2:
        raise ManifestError("outputs must contain at least two output definitions")
    parsed: list[tuple[str, str, int]] = []
    names: set[str] = set()
    for index, item in enumerate(outputs):
        if not isinstance(item, dict):
            raise ManifestError(f"outputs[{index}] must be an object")
        _reject_unknown(item, {"name", "unit", "round"}, f"outputs[{index}]")
        name = _required_string(item, "name", f"outputs[{index}]")
        if not name.isidentifier() or name in _FUNCTIONS or name == "value":
            raise ManifestError(f"outputs[{index}].name must be a non-reserved identifier")
        if name in names:
            raise ManifestError(f"duplicate output name: {name}")
        names.add(name)
        unit = _required_string(item, "unit", f"outputs[{index}]")
        digits = item.get("round", 4)
        if isinstance(digits, bool) or not isinstance(digits, int) or not 0 <= digits <= 10:
            raise ManifestError(f"outputs[{index}].round must be an integer from 0 to 10")
        parsed.append((name, unit, digits))
    unit_summary = "; ".join(f"{name}={unit}" for name, unit, _ in parsed)
    return tuple(parsed), True, unit_summary


def _compile_calculation(
    raw: dict[str, Any],
    schema_version: int,
    parsed_inputs: list[tuple[InputSpec, dict[str, Any]]],
    output_names: tuple[str, ...],
    multi_output: bool,
) -> tuple[str, str, Callable[[dict[str, Any]], tuple[Any, str | None]]]:
    input_names = {spec.name for spec, _ in parsed_inputs}
    specs = {spec.name: spec for spec, _ in parsed_inputs}

    def parse_row_result(mapping: dict[str, Any], context: str) -> Any:
        if multi_output:
            if "value" in mapping:
                raise ManifestError(f"{context} must use values for multi-output calculators")
            values = mapping.get("values")
            if not isinstance(values, dict):
                raise ManifestError(f"{context}.values must be an object")
            missing = sorted(set(output_names) - set(values))
            unknown = sorted(set(values) - set(output_names))
            if missing or unknown:
                details = []
                if missing:
                    details.append(f"missing {', '.join(missing)}")
                if unknown:
                    details.append(f"unknown {', '.join(unknown)}")
                raise ManifestError(f"{context}.values: {'; '.join(details)}")
            return {
                name: _finite_number(values[name], f"{context}.values.{name}")
                for name in output_names
            }
        if "values" in mapping:
            raise ManifestError(f"{context} must use value for a scalar calculator")
        return _finite_number(mapping.get("value"), f"{context}.value")

    if schema_version == 1:
        if "calculation" in raw:
            raise ManifestError("schema_version 1 uses formula instead of calculation")
        formula = raw.get("formula")
        if not isinstance(formula, dict):
            raise ManifestError("formula must be an object")
        _reject_unknown(formula, {"expression"}, "formula")
        expression_text = _required_string(formula, "expression", "formula")
        expression = SafeExpression(expression_text, input_names)

        def evaluate_formula(values: dict[str, Any]) -> tuple[float, str | None]:
            calculated = expression.evaluate(values)
            if isinstance(calculated, bool) or not isinstance(calculated, (int, float)):
                raise ValueError("formula result must be numeric")
            calculated = float(calculated)
            if not math.isfinite(calculated):
                raise ValueError("formula result must be finite")
            return calculated, None

        return expression_text, "user-added declarative formula", evaluate_formula

    if "formula" in raw:
        raise ManifestError("schema_version 2 uses calculation instead of formula")
    calculation = raw.get("calculation")
    if not isinstance(calculation, dict):
        raise ManifestError("calculation must be an object for schema_version 2")
    calculation_type = calculation.get("type")

    if calculation_type == "formula":
        if multi_output:
            raise ManifestError("multi-output calculators must use calculation.type formula_set")
        _reject_unknown(calculation, {"type", "expression"}, "calculation")
        expression_text = _required_string(calculation, "expression", "calculation")
        expression = SafeExpression(expression_text, input_names)

        def evaluate_formula_v2(values: dict[str, Any]) -> tuple[float, str | None]:
            calculated = expression.evaluate(values)
            if isinstance(calculated, bool) or not isinstance(calculated, (int, float)):
                raise ValueError("formula result must be numeric")
            calculated = float(calculated)
            if not math.isfinite(calculated):
                raise ValueError("formula result must be finite")
            return calculated, None

        return expression_text, "user-added versioned formula", evaluate_formula_v2

    if calculation_type == "formula_set":
        if not multi_output:
            raise ManifestError("calculation.type formula_set requires outputs")
        _reject_unknown(calculation, {"type", "expressions"}, "calculation")
        expressions = calculation.get("expressions")
        if not isinstance(expressions, dict):
            raise ManifestError("calculation.expressions must be an object")
        missing = sorted(set(output_names) - set(expressions))
        unknown = sorted(set(expressions) - set(output_names))
        if missing or unknown:
            details = []
            if missing:
                details.append(f"missing {', '.join(missing)}")
            if unknown:
                details.append(f"unknown {', '.join(unknown)}")
            raise ManifestError(f"calculation.expressions: {'; '.join(details)}")
        compiled_expressions = {
            name: SafeExpression(
                _required_string(expressions, name, "calculation.expressions"), input_names
            )
            for name in output_names
        }

        def evaluate_formula_set(values: dict[str, Any]) -> tuple[dict[str, float], str | None]:
            calculated: dict[str, float] = {}
            for name, expression in compiled_expressions.items():
                value = expression.evaluate(values)
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError(f"formula result {name} must be numeric")
                value = float(value)
                if not math.isfinite(value):
                    raise ValueError(f"formula result {name} must be finite")
                calculated[name] = value
            return calculated, None

        return (
            "formula set: " + "; ".join(
                f"{name}={compiled_expressions[name].expression}" for name in output_names
            ),
            "user-added versioned multi-output formula",
            evaluate_formula_set,
        )

    if calculation_type == "lookup_table":
        _reject_unknown(calculation, {"type", "input", "match", "rows"}, "calculation")
        input_name = _required_string(calculation, "input", "calculation")
        if input_name not in specs:
            raise ManifestError(f"calculation.input is not a declared input: {input_name}")
        match = calculation.get("match")
        if match not in {"exact", "range"}:
            raise ManifestError("calculation.match must be exact or range")
        rows = calculation.get("rows")
        if not isinstance(rows, list) or not rows:
            raise ManifestError("calculation.rows must be a non-empty list")

        if match == "exact":
            compiled_exact: dict[Any, tuple[Any, str | None]] = {}
            spec = specs[input_name]
            for index, row in enumerate(rows):
                if not isinstance(row, dict):
                    raise ManifestError(f"calculation.rows[{index}] must be an object")
                _reject_unknown(
                    row,
                    {"key", "value", "values", "interpretation"},
                    f"calculation.rows[{index}]",
                )
                if "key" not in row:
                    raise ManifestError(f"calculation.rows[{index}].key is required")
                key = row["key"]
                if spec.value_type == "number":
                    key = _finite_number(key, f"calculation.rows[{index}].key")
                elif spec.value_type == "boolean":
                    if not isinstance(key, bool):
                        raise ManifestError(f"calculation.rows[{index}].key must be boolean")
                else:
                    if not isinstance(key, str) or key not in spec.choices:
                        raise ManifestError(
                            f"calculation.rows[{index}].key must be one of: {', '.join(spec.choices)}"
                        )
                if key in compiled_exact:
                    raise ManifestError(f"duplicate exact lookup key: {key}")
                value = parse_row_result(row, f"calculation.rows[{index}]")
                interpretation = row.get("interpretation")
                if interpretation is not None and (
                    not isinstance(interpretation, str) or not interpretation.strip()
                ):
                    raise ManifestError(
                        f"calculation.rows[{index}].interpretation must be a non-empty string"
                    )
                compiled_exact[key] = (value, interpretation.strip() if interpretation else None)

            def evaluate_exact(values: dict[str, Any]) -> tuple[Any, str | None]:
                key = values[input_name]
                if key not in compiled_exact:
                    raise ValueError(f"no exact lookup row for {input_name}={key}")
                return compiled_exact[key]

            return (
                f"exact lookup table on {input_name}",
                "user-added versioned exact lookup table",
                evaluate_exact,
            )

        if specs[input_name].value_type != "number":
            raise ManifestError("range lookup requires a number input")
        compiled_ranges: list[tuple[float, float, bool, bool, Any, str | None]] = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ManifestError(f"calculation.rows[{index}] must be an object")
            _reject_unknown(
                row,
                {
                    "minimum",
                    "maximum",
                    "include_minimum",
                    "include_maximum",
                    "value",
                    "values",
                    "interpretation",
                },
                f"calculation.rows[{index}]",
            )
            if "minimum" not in row and "maximum" not in row:
                raise ManifestError(
                    f"calculation.rows[{index}] requires minimum or maximum"
                )
            minimum = (
                -math.inf
                if "minimum" not in row
                else _finite_number(row["minimum"], f"calculation.rows[{index}].minimum")
            )
            maximum = (
                math.inf
                if "maximum" not in row
                else _finite_number(row["maximum"], f"calculation.rows[{index}].maximum")
            )
            include_minimum = row.get("include_minimum", True)
            include_maximum = row.get("include_maximum", False)
            if not isinstance(include_minimum, bool) or not isinstance(include_maximum, bool):
                raise ManifestError(
                    f"calculation.rows[{index}] include_minimum/include_maximum must be boolean"
                )
            if minimum > maximum or (
                minimum == maximum and not (include_minimum and include_maximum)
            ):
                raise ManifestError(f"calculation.rows[{index}] has an empty range")
            value = parse_row_result(row, f"calculation.rows[{index}]")
            interpretation = row.get("interpretation")
            if interpretation is not None and (
                not isinstance(interpretation, str) or not interpretation.strip()
            ):
                raise ManifestError(
                    f"calculation.rows[{index}].interpretation must be a non-empty string"
                )
            compiled_ranges.append(
                (
                    minimum,
                    maximum,
                    include_minimum,
                    include_maximum,
                    value,
                    interpretation.strip() if interpretation else None,
                )
            )
        for left_index, left in enumerate(compiled_ranges):
            for right_index, right in enumerate(compiled_ranges[left_index + 1 :], left_index + 1):
                low = max(left[0], right[0])
                high = min(left[1], right[1])
                overlaps = low < high
                if low == high:
                    left_contains = (low > left[0] or left[2]) and (low < left[1] or left[3])
                    right_contains = (low > right[0] or right[2]) and (low < right[1] or right[3])
                    overlaps = left_contains and right_contains
                if overlaps:
                    raise ManifestError(
                        f"calculation range rows overlap: {left_index} and {right_index}"
                    )

        def evaluate_range(values: dict[str, Any]) -> tuple[Any, str | None]:
            candidate = values[input_name]
            matches = [
                row
                for row in compiled_ranges
                if (candidate > row[0] or (row[2] and candidate == row[0]))
                and (candidate < row[1] or (row[3] and candidate == row[1]))
            ]
            if not matches:
                raise ValueError(f"no range lookup row for {input_name}={candidate:g}")
            return matches[0][4], matches[0][5]

        return (
            f"non-interpolating range lookup table on {input_name}",
            "user-added versioned range lookup table",
            evaluate_range,
        )

    if calculation_type == "multidimensional_lookup":
        _reject_unknown(calculation, {"type", "dimensions", "rows"}, "calculation")
        dimensions = calculation.get("dimensions")
        if not isinstance(dimensions, list) or len(dimensions) < 2:
            raise ManifestError("calculation.dimensions must contain at least two dimensions")
        compiled_dimensions: list[tuple[str, str]] = []
        dimension_names: set[str] = set()
        for index, dimension in enumerate(dimensions):
            if not isinstance(dimension, dict):
                raise ManifestError(f"calculation.dimensions[{index}] must be an object")
            _reject_unknown(
                dimension, {"input", "match"}, f"calculation.dimensions[{index}]"
            )
            name = _required_string(
                dimension, "input", f"calculation.dimensions[{index}]"
            )
            if name not in specs:
                raise ManifestError(
                    f"calculation.dimensions[{index}].input is not declared: {name}"
                )
            if name in dimension_names:
                raise ManifestError(f"duplicate lookup dimension: {name}")
            dimension_names.add(name)
            match = dimension.get("match")
            if match not in {"exact", "range"}:
                raise ManifestError(
                    f"calculation.dimensions[{index}].match must be exact or range"
                )
            if match == "range" and specs[name].value_type != "number":
                raise ManifestError(f"range lookup dimension {name} requires a number input")
            compiled_dimensions.append((name, match))

        def normalize_exact_key(value: Any, spec: InputSpec, context: str) -> Any:
            if spec.value_type == "number":
                return _finite_number(value, context)
            if spec.value_type == "boolean":
                if not isinstance(value, bool):
                    raise ManifestError(f"{context} must be boolean")
                return value
            if not isinstance(value, str) or value not in spec.choices:
                raise ManifestError(f"{context} must be one of: {', '.join(spec.choices)}")
            return value

        def compile_range_key(value: Any, context: str) -> tuple[float, float, bool, bool]:
            if not isinstance(value, dict):
                raise ManifestError(f"{context} must be a range object")
            _reject_unknown(
                value,
                {"minimum", "maximum", "include_minimum", "include_maximum"},
                context,
            )
            if "minimum" not in value and "maximum" not in value:
                raise ManifestError(f"{context} requires minimum or maximum")
            minimum = (
                -math.inf
                if "minimum" not in value
                else _finite_number(value["minimum"], f"{context}.minimum")
            )
            maximum = (
                math.inf
                if "maximum" not in value
                else _finite_number(value["maximum"], f"{context}.maximum")
            )
            include_minimum = value.get("include_minimum", True)
            include_maximum = value.get("include_maximum", False)
            if not isinstance(include_minimum, bool) or not isinstance(include_maximum, bool):
                raise ManifestError(
                    f"{context} include_minimum/include_maximum must be boolean"
                )
            if minimum > maximum or (
                minimum == maximum and not (include_minimum and include_maximum)
            ):
                raise ManifestError(f"{context} has an empty range")
            return minimum, maximum, include_minimum, include_maximum

        def ranges_overlap(
            left: tuple[float, float, bool, bool],
            right: tuple[float, float, bool, bool],
        ) -> bool:
            low = max(left[0], right[0])
            high = min(left[1], right[1])
            if low < high:
                return True
            if low != high:
                return False
            left_contains = (low > left[0] or left[2]) and (low < left[1] or left[3])
            right_contains = (low > right[0] or right[2]) and (
                low < right[1] or right[3]
            )
            return left_contains and right_contains

        rows = calculation.get("rows")
        if not isinstance(rows, list) or not rows:
            raise ManifestError("calculation.rows must be a non-empty list")
        compiled_rows: list[tuple[dict[str, Any], Any, str | None]] = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ManifestError(f"calculation.rows[{index}] must be an object")
            _reject_unknown(
                row,
                {"keys", "value", "values", "interpretation"},
                f"calculation.rows[{index}]",
            )
            keys = row.get("keys")
            if not isinstance(keys, dict):
                raise ManifestError(f"calculation.rows[{index}].keys must be an object")
            missing = sorted(dimension_names - set(keys))
            unknown = sorted(set(keys) - dimension_names)
            if missing or unknown:
                details = []
                if missing:
                    details.append(f"missing {', '.join(missing)}")
                if unknown:
                    details.append(f"unknown {', '.join(unknown)}")
                raise ManifestError(
                    f"calculation.rows[{index}].keys: {'; '.join(details)}"
                )
            compiled_keys: dict[str, Any] = {}
            for name, match in compiled_dimensions:
                context = f"calculation.rows[{index}].keys.{name}"
                compiled_keys[name] = (
                    normalize_exact_key(keys[name], specs[name], context)
                    if match == "exact"
                    else compile_range_key(keys[name], context)
                )
            result = parse_row_result(row, f"calculation.rows[{index}]")
            interpretation = row.get("interpretation")
            if interpretation is not None and (
                not isinstance(interpretation, str) or not interpretation.strip()
            ):
                raise ManifestError(
                    f"calculation.rows[{index}].interpretation must be a non-empty string"
                )
            compiled_rows.append(
                (compiled_keys, result, interpretation.strip() if interpretation else None)
            )

        for left_index, left in enumerate(compiled_rows):
            for right_index, right in enumerate(compiled_rows[left_index + 1 :], left_index + 1):
                overlaps_in_every_dimension = True
                for name, match in compiled_dimensions:
                    if match == "exact":
                        dimension_overlap = left[0][name] == right[0][name]
                    else:
                        dimension_overlap = ranges_overlap(left[0][name], right[0][name])
                    if not dimension_overlap:
                        overlaps_in_every_dimension = False
                        break
                if overlaps_in_every_dimension:
                    raise ManifestError(
                        f"multidimensional lookup rows overlap: {left_index} and {right_index}"
                    )

        def evaluate_multidimensional(values: dict[str, Any]) -> tuple[Any, str | None]:
            matches: list[tuple[dict[str, Any], Any, str | None]] = []
            for row in compiled_rows:
                matched = True
                for name, match in compiled_dimensions:
                    if match == "exact":
                        dimension_match = values[name] == row[0][name]
                    else:
                        minimum, maximum, include_minimum, include_maximum = row[0][name]
                        candidate = values[name]
                        dimension_match = (
                            candidate > minimum
                            or (include_minimum and candidate == minimum)
                        ) and (
                            candidate < maximum
                            or (include_maximum and candidate == maximum)
                        )
                    if not dimension_match:
                        matched = False
                        break
                if matched:
                    matches.append(row)
            if not matches:
                rendered = ", ".join(f"{name}={values[name]}" for name, _ in compiled_dimensions)
                raise ValueError(f"no multidimensional lookup row for {rendered}")
            return matches[0][1], matches[0][2]

        return (
            "non-interpolating multidimensional lookup on "
            + ", ".join(f"{name}:{match}" for name, match in compiled_dimensions),
            "user-added versioned multidimensional lookup table",
            evaluate_multidimensional,
        )

    if calculation_type == "decision_tree":
        _reject_unknown(calculation, {"type", "rules", "default"}, "calculation")
        rules = calculation.get("rules")
        if not isinstance(rules, list) or not rules:
            raise ManifestError("calculation.rules must be a non-empty list")
        compiled_decisions: list[tuple[SafeExpression, Any, str | None]] = []
        for index, rule in enumerate(rules):
            if not isinstance(rule, dict):
                raise ManifestError(f"calculation.rules[{index}] must be an object")
            _reject_unknown(
                rule,
                {"when", "value", "values", "interpretation"},
                f"calculation.rules[{index}]",
            )
            condition = SafeExpression(
                _required_string(rule, "when", f"calculation.rules[{index}]"), input_names
            )
            value = parse_row_result(rule, f"calculation.rules[{index}]")
            interpretation = rule.get("interpretation")
            if interpretation is not None and (
                not isinstance(interpretation, str) or not interpretation.strip()
            ):
                raise ManifestError(
                    f"calculation.rules[{index}].interpretation must be a non-empty string"
                )
            compiled_decisions.append(
                (condition, value, interpretation.strip() if interpretation else None)
            )
        default = calculation.get("default")
        if not isinstance(default, dict):
            raise ManifestError("calculation.default must be an object")
        _reject_unknown(
            default, {"value", "values", "interpretation"}, "calculation.default"
        )
        default_value = parse_row_result(default, "calculation.default")
        default_text = default.get("interpretation")
        if default_text is not None and (
            not isinstance(default_text, str) or not default_text.strip()
        ):
            raise ManifestError("calculation.default.interpretation must be a non-empty string")

        def evaluate_decision(values: dict[str, Any]) -> tuple[Any, str | None]:
            for condition, value, interpretation in compiled_decisions:
                if bool(condition.evaluate(values)):
                    return value, interpretation
            return default_value, default_text.strip() if default_text else None

        return (
            "ordered decision tree",
            "user-added versioned decision tree",
            evaluate_decision,
        )

    raise ManifestError(
        "calculation.type must be formula, formula_set, lookup_table, "
        "multidimensional_lookup, or decision_tree"
    )


def load_custom_manifest(path: str | Path) -> CustomCalculatorDefinition:
    manifest_path = Path(path)
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot read {manifest_path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ManifestError("manifest root must be an object")
    _reject_unknown(
        raw,
        {
            "schema_version",
            "id",
            "category",
            "subspecialty",
            "scenario",
            "name_cn",
            "name_en",
            "purpose",
            "inputs",
            "output",
            "outputs",
            "formula",
            "calculation",
            "interpretation",
            "default_interpretation",
            "test_cases",
            "clinical_note",
            "commonness",
            "notes",
            "source",
        },
        "manifest",
    )
    schema_version = raw.get("schema_version")
    if schema_version not in {1, 2}:
        raise ManifestError("schema_version must be 1 or 2")
    calculator_id = _required_string(raw, "id")
    if not CUSTOM_ID_PATTERN.fullmatch(calculator_id):
        raise ManifestError("id must be CUSTOM- followed by 3-64 uppercase letters, digits, or hyphens")

    raw_inputs = raw.get("inputs")
    if not isinstance(raw_inputs, list) or not raw_inputs:
        raise ManifestError("inputs must be a non-empty list")
    parsed_inputs = [_validate_input_definition(item, index) for index, item in enumerate(raw_inputs)]
    input_schema = tuple(item[0] for item in parsed_inputs)
    input_names = tuple(spec.name for spec in input_schema)
    if len(set(input_names)) != len(input_names):
        raise ManifestError("input names must be unique")

    output_fields, multi_output, unit = _validate_outputs(raw, schema_version)
    output_names = tuple(name for name, _, _ in output_fields)
    output_input_collisions = sorted(set(output_names) & set(input_names))
    if multi_output and output_input_collisions:
        raise ManifestError(
            "output names cannot duplicate input names: "
            + ", ".join(output_input_collisions)
        )
    calculation_text, coverage_note, calculation = _compile_calculation(
        raw, schema_version, parsed_inputs, output_names, multi_output
    )

    interpretation_rules = raw.get("interpretation", [])
    if not isinstance(interpretation_rules, list):
        raise ManifestError("interpretation must be a list")
    compiled_rules: list[tuple[SafeExpression, str]] = []
    for index, rule in enumerate(interpretation_rules):
        if not isinstance(rule, dict):
            raise ManifestError(f"interpretation[{index}] must be an object")
        _reject_unknown(rule, {"when", "text"}, f"interpretation[{index}]")
        interpretation_names = set(input_names) | (
            set(output_names) if multi_output else {"value"}
        )
        condition = SafeExpression(
            _required_string(rule, "when", f"interpretation[{index}]"),
            interpretation_names,
        )
        text = _required_string(rule, "text", f"interpretation[{index}]")
        compiled_rules.append((condition, text))
    default_interpretation = _required_string(raw, "default_interpretation")

    source = raw.get("source")
    if not isinstance(source, dict):
        raise ManifestError("source must be an object")
    _reject_unknown(
        source,
        {
            "type",
            "name",
            "url",
            "version",
            "evidence_tier",
            "effective_date",
            "retrieved_at",
        },
        "source",
    )
    source_url = _required_string(source, "url", "source")
    if not source_url.startswith(("http://", "https://")):
        raise ManifestError("source.url must start with http:// or https://")
    version = _required_string(source, "version", "source")
    source_dates: list[str] = []
    for key in ("effective_date", "retrieved_at"):
        value = source.get(key)
        if value is None:
            continue
        if not isinstance(value, str):
            raise ManifestError(f"source.{key} must be an ISO date (YYYY-MM-DD)")
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise ManifestError(f"source.{key} must be an ISO date (YYYY-MM-DD)") from exc
        source_dates.append(f"{key}={value}")

    metadata = CalculatorMetadata(
        id=calculator_id,
        category=_required_string(raw, "category"),
        subspecialty=str(raw.get("subspecialty", "")).strip(),
        scenario=_required_string(raw, "scenario"),
        name_cn=_required_string(raw, "name_cn"),
        name_en=_required_string(raw, "name_en"),
        inputs="; ".join(input_names),
        output=(
            "; ".join(f"{name} ({field_unit})" for name, field_unit, _ in output_fields)
            if multi_output
            else f"value ({unit})"
        ),
        formula=calculation_text,
        interpretation="; ".join(text for _, text in compiled_rules) or default_interpretation or "numeric result",
        purpose=_required_string(raw, "purpose"),
        source_type=str(source.get("type", "custom source")).strip() or "custom source",
        source=_required_string(source, "name", "source"),
        source_url=source_url,
        channel="user custom extension",
        evidence_tier=str(source.get("evidence_tier", "custom; requires review")).strip()
        or "custom; requires review",
        commonness=str(raw.get("commonness", "custom")).strip() or "custom",
        coverage_note=coverage_note,
        clinical_note=str(
            raw.get(
                "clinical_note",
                "Decision support only; independently verify before clinical use.",
            )
        ).strip()
        or "Decision support only; independently verify before clinical use.",
        version=version,
        entry_source="custom manifest",
        source_group="custom",
        notes="; ".join(
            item
            for item in (str(raw.get("notes", "")).strip(), *source_dates)
            if item
        ),
    )

    def implementation(meta: CalculatorMetadata, inputs: dict[str, Any]) -> CalculationResult:
        values = {
            spec.name: _validate_runtime_input(spec, input_raw, inputs[spec.name])
            for (spec, input_raw) in parsed_inputs
        }
        calculated, branch_interpretation = calculation(values)
        if multi_output:
            if not isinstance(calculated, dict) or set(calculated) != set(output_names):
                raise ValueError("multi-output calculation returned invalid fields")
            rounded: Any = {
                name: round(float(calculated[name]), digits)
                for name, _, digits in output_fields
            }
            rule_values = {**values, **rounded}
        else:
            digits = output_fields[0][2]
            rounded = round(float(calculated), digits)
            rule_values = {**values, "value": rounded}
        interpretation = branch_interpretation or default_interpretation
        if not branch_interpretation:
            for condition, text in compiled_rules:
                if bool(condition.evaluate(rule_values)):
                    interpretation = text
                    break
        return CalculationResult(
            calculator_id=meta.id,
            status="implemented",
            message="custom calculation completed",
            value=rounded,
            unit=unit,
            interpretation=interpretation,
        )

    implementation.__name__ = f"custom_{calculator_id.lower().replace('-', '_')}"
    implementation.__module__ = __name__
    definition = CustomCalculatorDefinition(
        metadata, implementation, input_names, input_schema, manifest_path
    )

    test_cases = raw.get("test_cases", [])
    if not isinstance(test_cases, list):
        raise ManifestError("test_cases must be a list")
    if schema_version == 2 and not test_cases:
        raise ManifestError("schema_version 2 requires at least one source-derived test case")
    for index, test_case in enumerate(test_cases):
        if not isinstance(test_case, dict):
            raise ManifestError(f"test_cases[{index}] must be an object")
        _reject_unknown(
            test_case,
            {
                "name",
                "inputs",
                "expected_value",
                "expected_values",
                "tolerance",
                "expected_interpretation",
            },
            f"test_cases[{index}]",
        )
        _required_string(test_case, "name", f"test_cases[{index}]")
        case_inputs = test_case.get("inputs")
        if not isinstance(case_inputs, dict):
            raise ManifestError(f"test_cases[{index}].inputs must be an object")
        missing = sorted(set(input_names) - set(case_inputs))
        unknown = sorted(set(case_inputs) - set(input_names))
        if missing or unknown:
            details = []
            if missing:
                details.append(f"missing {', '.join(missing)}")
            if unknown:
                details.append(f"unknown {', '.join(unknown)}")
            raise ManifestError(f"test_cases[{index}].inputs: {'; '.join(details)}")
        if multi_output:
            if "expected_value" in test_case:
                raise ManifestError(
                    f"test_cases[{index}] must use expected_values for multiple outputs"
                )
            expected_values = test_case.get("expected_values")
            if not isinstance(expected_values, dict):
                raise ManifestError(f"test_cases[{index}].expected_values must be an object")
            expected_missing = sorted(set(output_names) - set(expected_values))
            expected_unknown = sorted(set(expected_values) - set(output_names))
            if expected_missing or expected_unknown:
                details = []
                if expected_missing:
                    details.append(f"missing {', '.join(expected_missing)}")
                if expected_unknown:
                    details.append(f"unknown {', '.join(expected_unknown)}")
                raise ManifestError(
                    f"test_cases[{index}].expected_values: {'; '.join(details)}"
                )
            expected: Any = {
                name: _finite_number(
                    expected_values[name], f"test_cases[{index}].expected_values.{name}"
                )
                for name in output_names
            }
        else:
            if "expected_values" in test_case:
                raise ManifestError(
                    f"test_cases[{index}] must use expected_value for a scalar output"
                )
            expected = _finite_number(
                test_case.get("expected_value"), f"test_cases[{index}].expected_value"
            )
        tolerance = _finite_number(
            test_case.get("tolerance", 0), f"test_cases[{index}].tolerance"
        )
        if tolerance < 0:
            raise ManifestError(f"test_cases[{index}].tolerance must be nonnegative")
        try:
            result = implementation(metadata, case_inputs)
        except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
            raise ManifestError(f"test_cases[{index}] failed to run: {exc}") from exc
        if multi_output:
            if not isinstance(result.value, dict):
                raise ManifestError(f"test_cases[{index}] did not return multiple outputs")
            mismatches = [
                name
                for name in output_names
                if abs(float(result.value[name]) - expected[name]) > tolerance
            ]
            if mismatches:
                raise ManifestError(
                    f"test_cases[{index}] output mismatch for {', '.join(mismatches)}: "
                    f"expected {expected}, got {result.value}"
                )
        elif abs(float(result.value) - expected) > tolerance:
            raise ManifestError(
                f"test_cases[{index}] expected {expected:g} ± {tolerance:g}, got {result.value}"
            )
        expected_interpretation = test_case.get("expected_interpretation")
        if expected_interpretation is not None:
            if not isinstance(expected_interpretation, str) or not expected_interpretation.strip():
                raise ManifestError(
                    f"test_cases[{index}].expected_interpretation must be a non-empty string"
                )
            if result.interpretation != expected_interpretation.strip():
                raise ManifestError(
                    f"test_cases[{index}] interpretation mismatch: {result.interpretation!r}"
                )
    return definition


def custom_directories(extra_dirs: Iterable[str | Path] | None = None) -> list[Path]:
    directories = [DEFAULT_CUSTOM_DIR]
    configured = os.environ.get(CUSTOM_DIRS_ENV, "")
    directories.extend(Path(item) for item in configured.split(os.pathsep) if item)
    if extra_dirs:
        directories.extend(Path(item) for item in extra_dirs)
    unique: list[Path] = []
    seen: set[Path] = set()
    for directory in directories:
        resolved = directory.expanduser().resolve()
        if resolved not in seen:
            unique.append(resolved)
            seen.add(resolved)
    return unique


def discover_custom_calculators(
    extra_dirs: Iterable[str | Path] | None = None,
) -> list[CustomCalculatorDefinition]:
    definitions: list[CustomCalculatorDefinition] = []
    seen_ids: dict[str, Path] = {}
    for directory in custom_directories(extra_dirs):
        if not directory.exists():
            continue
        if not directory.is_dir():
            raise ManifestError(f"custom calculator path is not a directory: {directory}")
        for manifest_path in sorted(directory.glob("*.json")):
            definition = load_custom_manifest(manifest_path)
            prior = seen_ids.get(definition.metadata.id)
            if prior:
                raise ManifestError(
                    f"duplicate custom calculator id {definition.metadata.id}: {prior} and {manifest_path}"
                )
            seen_ids[definition.metadata.id] = manifest_path
            definitions.append(definition)
    return definitions


__all__ = [
    "CUSTOM_DIRS_ENV",
    "DEFAULT_CUSTOM_DIR",
    "CustomCalculatorDefinition",
    "ManifestError",
    "SafeExpression",
    "custom_directories",
    "discover_custom_calculators",
    "load_custom_manifest",
]
