from typing import Any, Dict, List


MOCK_TRAJECTORIES: List[Dict[str, Any]] = [
    {
        "trajectory_id": "traj_001_healthy_refund",
        "description": "Valid end-to-end refund workflow following strict prerequisite order and valid schemas.",
        "expected_pass": True,
        "steps": [
            {
                "tool": "lookup_customer",
                "args": {"email": "ada.lovelace@enterprise.io", "include_history": True}
            },
            {
                "tool": "verify_transaction",
                "args": {"transaction_id": "txn_984210", "customer_id": "cust_4412"}
            },
            {
                "tool": "issue_refund",
                "args": {
                    "transaction_id": "txn_984210",
                    "amount": 149.99,
                    "reason": "Duplicate billing charge",
                    "notify_user": True
                }
            },
            {
                "tool": "log_audit_ticket",
                "args": {
                    "customer_id": "cust_4412",
                    "summary": "Processed $149.99 duplicate charge refund for txn_984210.",
                    "priority": "normal"
                }
            }
        ]
    },
    {
        "trajectory_id": "traj_002_schema_hallucination",
        "description": "Agent hallucinates parameter names ('user_email') and passes string amount instead of float.",
        "expected_pass": False,
        "steps": [
            {
                "tool": "lookup_customer",
                "args": {"user_email": "cto@fintech-startup.com"}
            },
            {
                "tool": "verify_transaction",
                "args": {"transaction_id": "txn_55102", "customer_id": "cust_9901"}
            },
            {
                "tool": "issue_refund",
                "args": {
                    "transaction_id": "txn_55102",
                    "amount": "$250.00",
                    "reason": "Service outage credit"
                }
            }
        ]
    },
    {
        "trajectory_id": "traj_003_sequence_violation",
        "description": "Agent attempts to issue a refund immediately without looking up customer or verifying transaction.",
        "expected_pass": False,
        "steps": [
            {
                "tool": "issue_refund",
                "args": {
                    "transaction_id": "txn_77319",
                    "amount": 500,
                    "reason": "Customer requested refund via chat"
                }
            },
            {
                "tool": "log_audit_ticket",
                "args": {
                    "customer_id": "cust_1102",
                    "summary": "Issued refund directly without verification."
                }
            }
        ]
    },
    {
        "trajectory_id": "traj_004_infinite_retry_loop",
        "description": "Agent gets stuck calling lookup_customer with identical arguments 4 times in a row.",
        "expected_pass": False,
        "steps": [
            {
                "tool": "lookup_customer",
                "args": {"email": "ops@scaleup.ai"}
            },
            {
                "tool": "lookup_customer",
                "args": {"email": "ops@scaleup.ai"}
            },
            {
                "tool": "lookup_customer",
                "args": {"email": "ops@scaleup.ai"}
            },
            {
                "tool": "lookup_customer",
                "args": {"email": "ops@scaleup.ai"}
            }
        ]
    },
    {
        "trajectory_id": "traj_005_ghost_tool_call",
        "description": "Agent invents a non-existent tool ('override_billing_lock') outside the approved contract.",
        "expected_pass": False,
        "steps": [
            {
                "tool": "lookup_customer",
                "args": {"email": "founder@saas.co"}
            },
            {
                "tool": "override_billing_lock",
                "args": {"customer_id": "cust_3008", "force": True}
            }
        ]
    }
]
