# 🛡️ Project 6: Agentic Trajectory & Tool-Call Hallucination Evaluator

A zero-dependency, deterministic evaluation engine that audits multi-step LLM agent execution trajectories before unsafe tool calls reach production.

## Why This Exists
In production AI agent deployments, models frequently return confident natural-language responses while failing silently in the tool-execution layer:
- **Schema & Type Hallucinations:** Inventing parameter names (`user_email` vs. `email`) or passing formatted strings (`"$250.00"`) into numeric fields.
- **Prerequisite Sequence Violations:** Calling high-impact mutating tools (`issue_refund`) before verification steps (`verify_transaction`).
- **Infinite Retry Loops:** Calling identical tools repeatedly with identical arguments, burning token budgets and spiking latency.
- **Ghost Tool Calls:** Fabricating non-existent tool names outside approved contracts.

## Quickstart

```bash
cd project6_agent_eval
python3 cli_runner.py
```

### Run as a CI/CD Quality Gate
```bash
python3 cli_runner.py --ci-gate
```

### Run Unit Tests
```bash
python3 -m unittest discover -v
```
