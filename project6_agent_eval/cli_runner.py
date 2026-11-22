import argparse
import sys
from typing import List
from config import AgentEvalConfig
from evaluator import EvaluationReport, TrajectoryEvaluator
from mock_trajectories import MOCK_TRAJECTORIES


def print_audit_table(reports: List[EvaluationReport], threshold: float) -> None:
    """Prints a clean, terminal-friendly audit summary table."""
    header = (
        f"{'TRAJECTORY ID':<32} | {'STATUS':<6} | {'SCORE':<6} | "
        f"{'SCHEMA':<6} | {'PREC':<6} | {'SEQ':<6} | {'LOOP':<6}"
    )
    separator = "-" * len(header)

    print("\n" + "=" * len(header))
    print(f"🛡️  HPS AGENTIC TRAJECTORY AUDIT REPORT (Pass Threshold: {threshold:.2f})")
    print("=" * len(header))
    print(header)
    print(separator)

    for rep in reports:
        status = "PASS" if rep.passed else "FAIL"
        print(
            f"{rep.trajectory_id:<32} | {status:<6} | {rep.composite_score:<6.2f} | "
            f"{rep.schema_validity_score:<6.2f} | {rep.tool_precision_score:<6.2f} | "
            f"{rep.sequence_order_score:<6.2f} | {rep.loop_efficiency_score:<6.2f}"
        )

    print(separator)

    print("\n🔍 DETAILED VIOLATION DIAGNOSTICS:")
    for rep in reports:
        if rep.violations:
            print(f"\n  ❌ {rep.trajectory_id} (Composite: {rep.composite_score:.2f}):")
            for v in rep.violations:
                print(f"     • {v}")
        else:
            print(f"\n  ✅ {rep.trajectory_id}: All contract checks passed.")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run deterministic trajectory evaluation on LLM agent execution logs."
    )
    parser.add_argument(
        "--ci-gate",
        action="store_true",
        help="Exit with code 1 if any trajectory fails to meet the quality threshold."
    )
    args = parser.parse_args()

    config = AgentEvalConfig()
    evaluator = TrajectoryEvaluator(config=config)
    reports: List[EvaluationReport] = []

    benchmark_mismatches = 0

    for item in MOCK_TRAJECTORIES:
        report = evaluator.evaluate(
            trajectory_id=item["trajectory_id"],
            steps=item["steps"]
        )
        reports.append(report)

        if report.passed != item["expected_pass"]:
            benchmark_mismatches += 1

    print_audit_table(reports, config.PASS_THRESHOLD)

    total = len(reports)
    passed_count = sum(1 for r in reports if r.passed)
    print(f"Summary: {passed_count}/{total} trajectories passed | Benchmark Mismatches: {benchmark_mismatches}")

    if args.ci_gate and passed_count < total:
        print("🚨 CI/CD QUALITY GATE FAILED: One or more agent trajectories violated contracts.")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
