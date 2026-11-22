import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple
from config import AgentEvalConfig


@dataclass
class EvaluationReport:
    """Structured audit report for a single agent execution trajectory."""
    trajectory_id: str
    passed: bool
    composite_score: float
    schema_validity_score: float
    tool_precision_score: float
    sequence_order_score: float
    loop_efficiency_score: float
    violations: List[str] = field(default_factory=list)


class TrajectoryEvaluator:
    """Audits multi-step LLM agent trajectories against strict tool contracts."""

    def __init__(self, config: AgentEvalConfig = AgentEvalConfig()):
        self.config = config
        self.contracts = config.TOOL_CONTRACTS

    def evaluate(self, trajectory_id: str, steps: List[Dict[str, Any]]) -> EvaluationReport:
        """
        Evaluates a sequence of tool calls.
        Expected step format: {"tool": str, "args": dict}
        """
        if not steps:
            return EvaluationReport(
                trajectory_id=trajectory_id,
                passed=False,
                composite_score=0.0,
                schema_validity_score=0.0,
                tool_precision_score=0.0,
                sequence_order_score=0.0,
                loop_efficiency_score=0.0,
                violations=["Empty trajectory: no tool calls recorded."]
            )

        violations: List[str] = []
        total_steps = len(steps)

        valid_tool_calls = 0
        valid_schema_calls = 0
        valid_sequence_calls = 0
        executed_tools: Set[str] = set()
        seen_signatures: Set[Tuple[str, str]] = set()
        redundant_calls = 0

        for idx, step in enumerate(steps):
            tool_name = step.get("tool", "")
            args = step.get("args", {})

            # 1. Check Tool Existence (Tool Precision)
            if tool_name not in self.contracts:
                violations.append(f"Step {idx + 1}: Unknown hallucinated tool '{tool_name}'.")
                continue

            valid_tool_calls += 1
            contract = self.contracts[tool_name]

            # 2. Check Parameter Schema & Types (Schema Validity)
            schema_ok, step_schema_errors = self._validate_schema(idx + 1, tool_name, args, contract)
            if schema_ok:
                valid_schema_calls += 1
            else:
                violations.extend(step_schema_errors)

            # 3. Check Prerequisite Execution Order (Sequence Order)
            prereqs = contract.get("prerequisites", [])
            missing_prereqs = [p for p in prereqs if p not in executed_tools]
            if not missing_prereqs:
                valid_sequence_calls += 1
            else:
                violations.append(
                    f"Step {idx + 1}: Sequence violation on '{tool_name}'. Missing prerequisites: {missing_prereqs}."
                )

            # 4. Detect Redundant / Infinite Retry Loops (Loop Efficiency)
            canonical_args = json.dumps(args, sort_keys=True, default=str)
            signature = (tool_name, canonical_args)
            if signature in seen_signatures:
                redundant_calls += 1
                violations.append(
                    f"Step {idx + 1}: Redundant duplicate call detected for '{tool_name}' with identical arguments."
                )
            else:
                seen_signatures.add(signature)

            # Mark tool as executed only if its schema was valid
            if schema_ok:
                executed_tools.add(tool_name)

        # Dimension Scores (0.0 to 1.0)
        tool_precision = valid_tool_calls / total_steps
        schema_validity = valid_schema_calls / total_steps
        sequence_order = valid_sequence_calls / total_steps
        loop_efficiency = max(0.0, (total_steps - redundant_calls) / total_steps)

        # Weighted Composite Score
        composite_score = round(
            (schema_validity * self.config.WEIGHT_SCHEMA_VALIDITY)
            + (tool_precision * self.config.WEIGHT_TOOL_PRECISION)
            + (sequence_order * self.config.WEIGHT_SEQUENCE_ORDER)
            + (loop_efficiency * self.config.WEIGHT_LOOP_EFFICIENCY),
            4
        )

        passed = composite_score >= self.config.PASS_THRESHOLD and len(violations) == 0

        return EvaluationReport(
            trajectory_id=trajectory_id,
            passed=passed,
            composite_score=composite_score,
            schema_validity_score=round(schema_validity, 4),
            tool_precision_score=round(tool_precision, 4),
            sequence_order_score=round(sequence_order, 4),
            loop_efficiency_score=round(loop_efficiency, 4),
            violations=violations
        )

    def _validate_schema(
        self, step_num: int, tool_name: str, args: Dict[str, Any], contract: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validates required keys, unexpected keys, and value data types."""
        errors: List[str] = []
        required = contract.get("required_params", {})
        optional = contract.get("optional_params", {})
        allowed_keys = set(required.keys()) | set(optional.keys())

        if not isinstance(args, dict):
            return False, [f"Step {step_num}: Arguments for '{tool_name}' must be a dictionary."]

        # Check for missing required parameters
        for req_key, expected_type in required.items():
            if req_key not in args:
                errors.append(f"Step {step_num}: '{tool_name}' missing required parameter '{req_key}'.")
            elif not self._is_valid_type(args[req_key], expected_type):
                errors.append(
                    f"Step {step_num}: '{tool_name}.{req_key}' expected {expected_type}, got {type(args[req_key]).__name__}."
                )

        # Check for hallucinated / unknown parameters
        for arg_key, arg_val in args.items():
            if arg_key not in allowed_keys:
                errors.append(f"Step {step_num}: '{tool_name}' received unexpected parameter '{arg_key}'.")
            elif arg_key in optional and not self._is_valid_type(arg_val, optional[arg_key]):
                errors.append(
                    f"Step {step_num}: '{tool_name}.{arg_key}' expected {optional[arg_key]}, got {type(arg_val).__name__}."
                )

        return len(errors) == 0, errors

    @staticmethod
    def _is_valid_type(value: Any, expected_type: Any) -> bool:
        """Handles Python's bool-is-int quirk during type validation."""
        if isinstance(value, bool) and expected_type is not bool:
            return False
        return isinstance(value, expected_type)
