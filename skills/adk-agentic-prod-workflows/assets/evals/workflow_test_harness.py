#!/usr/bin/env python3
"""Workflow evaluation harness — runs eval suites against ADK workflows.

Reads workflow-eval-config.yaml, executes each test case against the
target workflow, and reports pass/fail with detailed results.

Usage:
    python workflow_test_harness.py --config evals/eval-config.yaml
    python workflow_test_harness.py --config evals/eval-config.yaml --verbose
    python workflow_test_harness.py --config evals/eval-config.yaml --junitxml eval-results.xml
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class AssertionResult:
    field: str
    operator: str
    expected: Any
    actual: Any
    passed: bool

@dataclass
class CaseResult:
    case_id: str
    suite: str
    description: str
    passed: bool
    latency_ms: float
    assertions: list[AssertionResult] = field(default_factory=list)
    error: str | None = None
    workflow_result: dict | None = None

@dataclass
class SuiteResult:
    suite_name: str
    gate: str  # block | warn
    total: int
    passed: int
    cases: list[CaseResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total > 0 else 0.0


def evaluate_assertion(result: dict, assertion: dict) -> AssertionResult:
    """Evaluate a single assertion against workflow result."""
    field = assertion["field"]
    operator = assertion["operator"]
    expected = assertion.get("value")

    # Navigate nested fields: "data.user.name" → result["data"]["user"]["name"]
    actual = result
    for part in field.split("."):
        if isinstance(actual, dict):
            actual = actual.get(part)
        else:
            actual = None
            break

    operators: dict[str, Callable] = {
        "eq": lambda a, e: a == e,
        "neq": lambda a, e: a != e,
        "lt": lambda a, e: a is not None and a < e,
        "lte": lambda a, e: a is not None and a <= e,
        "gt": lambda a, e: a is not None and a > e,
        "gte": lambda a, e: a is not None and a >= e,
        "contains": lambda a, e: e in str(a) if a else False,
        "matches": lambda a, e: __import__("re").search(str(e), str(a)) if a else False,
        "exists": lambda a, _: a is not None,
    }

    op_fn = operators.get(operator)
    if op_fn is None:
        return AssertionResult(field, operator, expected, actual, False)

    passed = op_fn(actual, expected)
    return AssertionResult(field, operator, expected, actual, passed)


# ── Workflow Runner — override for your workflow ──────────────

async def run_workflow(query: str, params: dict | None = None) -> dict:
    """Execute the workflow. Override this for your specific workflow.

    In production, replace with actual ADK runner call:
        from app.workflow import graph_agent
        from google.adk.runners import InProcessRunner
        runner = InProcessRunner(agent=graph_agent)
        return await runner.run(query=query)
    """
    # Placeholder — replace with real workflow invocation
    start = time.monotonic()

    # Simulate workflow for template purposes
    if not query.strip():
        result = {"status": "error", "error": "Empty query"}
    elif "ignore previous instructions" in query.lower():
        result = {"status": "ok", "blocked": True}
    else:
        result = {"status": "ok", "data": {"processed": True}}

    result["latency_ms"] = (time.monotonic() - start) * 1000
    return result


# ── Main harness ────────────────────────────────────────

async def run_eval_suite(config: dict, verbose: bool = False) -> list[SuiteResult]:
    """Run all eval suites from config."""
    suite_results = []

    for suite_name, suite_cfg in config.get("eval_suites", {}).items():
        gate = suite_cfg.get("gate", "block")
        cases_cfg = suite_cfg.get("cases", [])
        suite = SuiteResult(suite_name, gate, len(cases_cfg), 0)

        for case_cfg in cases_cfg:
            case_id = case_cfg["id"]
            desc = case_cfg.get("description", "")

            start = time.monotonic()
            try:
                wf_result = await run_workflow(
                    case_cfg.get("input", {}).get("query", ""),
                    case_cfg.get("input", {}).get("params"),
                )
                elapsed = (time.monotonic() - start) * 1000

                assertions = []
                for a in case_cfg.get("assertions", []):
                    ar = evaluate_assertion(wf_result, a)
                    assertions.append(ar)

                passed = all(a.passed for a in assertions) if assertions else True

                cr = CaseResult(
                    case_id=case_id,
                    suite=suite_name,
                    description=desc,
                    passed=passed,
                    latency_ms=elapsed,
                    assertions=assertions,
                    workflow_result=wf_result,
                )
            except Exception as e:
                elapsed = (time.monotonic() - start) * 1000
                cr = CaseResult(
                    case_id=case_id,
                    suite=suite_name,
                    description=desc,
                    passed=False,
                    latency_ms=elapsed,
                    error=str(e),
                )

            suite.cases.append(cr)
            if cr.passed:
                suite.passed += 1

            if verbose:
                status = "PASS" if cr.passed else "FAIL"
                print(f"  [{status}] {suite_name}/{case_id}: {desc} ({cr.latency_ms:.0f}ms)")
                if cr.error:
                    print(f"    Error: {cr.error}")
                for a in cr.assertions:
                    if not a.passed:
                        print(f"    Assertion failed: {a.field} {a.operator} {a.expected} (got: {a.actual})")

        suite_results.append(suite)

    return suite_results


def print_report(suite_results: list[SuiteResult]) -> int:
    """Print evaluation report. Returns exit code."""
    total = sum(s.total for s in suite_results)
    passed = sum(s.passed for s in suite_results)
    rate = passed / total if total > 0 else 0.0

    blocked = False

    print(f"\n{'='*60}")
    print(f"Workflow Evaluation Report")
    print(f"{'='*60}\n")

    for suite in suite_results:
        gate_marker = "[GATE:BLOCK]" if suite.gate == "block" else "[GATE:WARN]"
        print(f"  {gate_marker} {suite.suite_name}: {suite.passed}/{suite.total} passed ({suite.pass_rate:.0%})")

    print(f"\n  Total: {passed}/{total} passed ({rate:.0%})")

    for suite in suite_results:
        if suite.gate == "block" and suite.pass_rate < 1.0:
            print(f"\n  Eval gate BLOCKED: suite '{suite.suite_name}' has failures (gate: block)")
            blocked = True
        elif suite.gate == "warn" and suite.pass_rate < 1.0:
            print(f"\n  Eval warning: suite '{suite.suite_name}' has failures (gate: warn — not blocking)")

    print()
    return 1 if blocked else 0


def write_junitxml(suite_results: list[SuiteResult], path: str) -> None:
    """Write JUnit XML report for CI integration."""
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    total = sum(s.total for s in suite_results)
    passed = sum(s.passed for s in suite_results)
    failed = total - passed
    xml.append(f'<testsuite name="adk-workflow-evals" tests="{total}" failures="{failed}">')

    for suite in suite_results:
        for case in suite.cases:
            status = "" if case.passed else f'<failure message="Eval failed">{case.error or ""}</failure>'
            xml.append(
                f'  <testcase name="{suite.suite_name}.{case.case_id}" '
                f'time="{case.latency_ms / 1000:.3f}">'
                f'{status}</testcase>'
            )

    xml.append("</testsuite>")
    Path(path).write_text("\n".join(xml))


def main():
    parser = argparse.ArgumentParser(description="ADK Workflow Evaluation Harness")
    parser.add_argument("--config", required=True, help="Eval configuration YAML file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--junitxml", help="Write JUnit XML report to file")
    parser.add_argument("--json", help="Write JSON report to file")

    args = parser.parse_args()

    if yaml is None:
        print("Error: PyYAML required. Install: pip install pyyaml")
        sys.exit(1)

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {args.config}")
        sys.exit(1)

    config = yaml.safe_load(config_path.read_text())

    import asyncio
    suite_results = asyncio.run(run_eval_suite(config, verbose=args.verbose))

    if args.json:
        import json as _json
        report = {
            "suites": [
                {
                    "name": s.suite_name,
                    "gate": s.gate,
                    "total": s.total,
                    "passed": s.passed,
                    "pass_rate": s.pass_rate,
                    "cases": [
                        {
                            "id": c.case_id,
                            "passed": c.passed,
                            "latency_ms": c.latency_ms,
                            "error": c.error,
                        }
                        for c in s.cases
                    ],
                }
                for s in suite_results
            ]
        }
        Path(args.json).write_text(_json.dumps(report, indent=2))

    if args.junitxml:
        write_junitxml(suite_results, args.junitxml)

    exit_code = print_report(suite_results)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
