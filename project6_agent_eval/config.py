from typing import Dict, Any, List

class AgentEvalConfig:
 """Configuration, tool contracts, and CI/CD quality thresholds for Agent Trajectory Evaluation."""

 # Minimum composite score (0.0 to 1.0) required to pass the CI/CD quality gate
 PASS_THRESHOLD: float = 0.85

 # Scoring weights across evaluation dimensions (must sum to 1.0)
 WEIGHT_SCHEMA_VALIDITY: float = 0.40
 WEIGHT_TOOL_PRECISION: float = 0.30
 WEIGHT_SEQUENCE_ORDER: float = 0.20
 WEIGHT_LOOP_EFFICIENCY: float = 0.10

 # Allowed tool contracts: defines required parameters, expected types, and prerequisite tools
 TOOL_CONTRACTS: Dict[str, Dict[str, Any]] = {
 "lookup_customer": {
 "required_params": {"email": str},
 "optional_params": {"include_history": bool},
 "prerequisites": []
 },
 "verify_transaction": {
 "required_params": {"transaction_id": str, "customer_id": str},
 "optional_params": {},
 "prerequisites": ["lookup_customer"]
 },
 "issue_refund": {
 "required_params": {"transaction_id": str, "amount": (int, float), "reason": str},
 "optional_params": {"notify_user": bool},
 "prerequisites": ["lookup_customer", "verify_transaction"]
 },
 "log_audit_ticket": {
 "required_params": {"customer_id": str, "summary": str},
 "optional_params": {"priority": str},
 "prerequisites": []
 }
 }