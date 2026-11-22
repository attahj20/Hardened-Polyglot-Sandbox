import unittest
from config import AgentEvalConfig
from evaluator import TrajectoryEvaluator
from mock_trajectories import MOCK_TRAJECTORIES


class TestTrajectoryEvaluator(unittest.TestCase):
    def setUp(self) -> None:
        self.evaluator = TrajectoryEvaluator(config=AgentEvalConfig())

    def test_mock_trajectories_match_expected_outcomes(self) -> None:
        for sample in MOCK_TRAJECTORIES:
            with self.subTest(trajectory_id=sample["trajectory_id"]):
                report = self.evaluator.evaluate(
                    trajectory_id=sample["trajectory_id"],
                    steps=sample["steps"]
                )
                self.assertEqual(
                    report.passed,
                    sample["expected_pass"],
                    f"{sample['trajectory_id']} expected passed={sample['expected_pass']}, "
                    f"got {report.passed} with violations: {report.violations}"
                )

    def test_empty_trajectory_fails(self) -> None:
        report = self.evaluator.evaluate("empty_run", [])
        self.assertFalse(report.passed)
        self.assertEqual(report.composite_score, 0.0)
        self.assertTrue(any("Empty trajectory" in v for v in report.violations))

    def test_bool_rejected_for_numeric_amount(self) -> None:
        """Ensures Python's bool-is-subclass-of-int quirk cannot bypass numeric schema checks."""
        steps = [
            {"tool": "lookup_customer", "args": {"email": "dev@company.com"}},
            {"tool": "verify_transaction", "args": {"transaction_id": "tx_1", "customer_id": "c_1"}},
            {
                "tool": "issue_refund",
                "args": {"transaction_id": "tx_1", "amount": True, "reason": "test"}
            }
        ]
        report = self.evaluator.evaluate("bool_injection_test", steps)
        self.assertFalse(report.passed)
        self.assertTrue(any("issue_refund.amount" in v for v in report.violations))


if __name__ == "__main__":
    unittest.main(verbosity=2)
