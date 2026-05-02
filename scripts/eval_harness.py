#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SUITES = (
    "trigger_recall",
    "trigger_precision",
    "archive_contract",
    "retrieval_quality",
    "compact_recovery",
    "cross_host",
)

POSITIVE_TRIGGER_GROUPS = {
    "should-trigger.txt": "trigger",
    "should-trigger-ascended.txt": "ascended",
}

CLI_SCRIPT = Path("scripts/mistakebook_cli.py")
LIFECYCLE_SCRIPT = Path("scripts/lifecycle_hooks.py")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_samples(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def load_matchers(root: Path) -> tuple[re.Pattern[str], re.Pattern[str]]:
    payload = read_json(root / "hooks" / "hooks.json")
    user_prompt_hooks = payload["hooks"]["UserPromptSubmit"]
    correction_matcher = re.compile(user_prompt_hooks[0]["matcher"])
    ascended_matcher = re.compile(user_prompt_hooks[1]["matcher"])
    return correction_matcher, ascended_matcher


def classify_prompt(sample: str, correction_matcher: re.Pattern[str], ascended_matcher: re.Pattern[str]) -> str:
    if ascended_matcher.search(sample):
        return "ascended"
    if correction_matcher.search(sample):
        return "correction"
    return "none"


def is_expected_trigger(expected: str, actual: str) -> bool:
    if expected == "trigger":
        return actual in {"correction", "ascended"}
    return expected == actual


def run_python(root: Path, script: Path, args: list[str], env: dict[str, str] | None = None) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(root / script), *args],
        text=True,
        capture_output=True,
        cwd=root,
        env=env or os.environ.copy(),
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "command failed").strip())
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"command returned invalid JSON: {completed.stdout}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("command returned non-object JSON")
    return payload


def run_python_raw(
    root: Path,
    script: Path,
    args: list[str],
    env: dict[str, str] | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(root / script), *args],
        input=input_text,
        text=True,
        capture_output=True,
        cwd=root,
        env=env or os.environ.copy(),
    )


def result(
    *,
    name: str,
    passed: bool,
    score: float | None = None,
    failures: list[dict[str, Any]] | None = None,
    **fields: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": name,
        "passed": passed,
        "failures": failures or [],
    }
    if score is not None:
        payload["score"] = round(score, 6)
    payload.update(fields)
    return payload


def evaluate_trigger_recall(root: Path, threshold: float) -> dict[str, Any]:
    correction_matcher, ascended_matcher = load_matchers(root)
    eval_dir = root / "evals" / "trigger-prompts"
    total = 0
    passed = 0
    failures: list[dict[str, Any]] = []

    for file_name, expected in POSITIVE_TRIGGER_GROUPS.items():
        for sample in load_samples(eval_dir / file_name):
            actual = classify_prompt(sample, correction_matcher, ascended_matcher)
            total += 1
            if is_expected_trigger(expected, actual):
                passed += 1
            else:
                failures.append(
                    {
                        "file": file_name,
                        "sample": sample,
                        "expected": expected,
                        "actual": actual,
                    }
                )

    score = passed / total if total else 1.0
    return result(
        name="trigger_recall",
        passed=score >= threshold,
        score=score,
        total=total,
        passedCount=passed,
        threshold=threshold,
        failures=failures,
    )


def evaluate_trigger_precision(root: Path, max_false_positive_rate: float) -> dict[str, Any]:
    correction_matcher, ascended_matcher = load_matchers(root)
    samples = load_samples(root / "evals" / "trigger-prompts" / "should-not-trigger.txt")
    failures: list[dict[str, Any]] = []
    passed = 0

    for sample in samples:
        actual = classify_prompt(sample, correction_matcher, ascended_matcher)
        if actual == "none":
            passed += 1
        else:
            failures.append({"sample": sample, "expected": "none", "actual": actual})

    total = len(samples)
    false_positive_rate = len(failures) / total if total else 0.0
    return result(
        name="trigger_precision",
        passed=false_positive_rate <= max_false_positive_rate,
        score=1.0 - false_positive_rate,
        total=total,
        passedCount=passed,
        falsePositiveRate=round(false_positive_rate, 6),
        maxFalsePositiveRate=max_false_positive_rate,
        failures=failures,
    )


def archive_payload(*, confirmed: bool = True, case_id: str = "archive-contract-case") -> dict[str, Any]:
    return {
        "entryType": "mistake",
        "caseId": case_id,
        "title": "archive contract case",
        "summary": "archive should wait for explicit user confirmation",
        "userConfirmed": confirmed,
        "scopeDecision": "project",
        "scopeReasoning": ["archive contract eval"],
        "rules": ["archive only after user confirmation"],
        "confirmedUnderstanding": ["confirmation is required before writing memory"],
        "originalPrompt": "user correction",
        "correctionFeedback": "not confirmed yet",
        "finalReply": "fixed reply",
    }


def evaluate_archive_contract(root: Path) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    details: dict[str, Any] = {}

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        unconfirmed_path = project_root / "unconfirmed.json"
        write_json(unconfirmed_path, archive_payload(confirmed=False))
        unconfirmed = run_python_raw(
            root,
            CLI_SCRIPT,
            [
                "archive",
                "--host",
                "codex",
                "--project-root",
                str(project_root),
                "--payload-file",
                str(unconfirmed_path),
            ],
        )
        checks["unconfirmedRejected"] = unconfirmed.returncode != 0
        details["unconfirmedOutput"] = (unconfirmed.stderr or unconfirmed.stdout).strip()

        state_path = project_root / "runtime_state.json"
        write_json(
            state_path,
            {
                "status": "pending_review",
                "entry_type": "mistake",
                "mode": "normal",
                "case_id": "archive-contract-case",
                "host": "codex",
                "project_root": str(project_root),
            },
        )
        confirmed_pending_path = project_root / "confirmed_pending.json"
        write_json(confirmed_pending_path, archive_payload(confirmed=True))
        pending = run_python_raw(
            root,
            CLI_SCRIPT,
            [
                "archive",
                "--host",
                "codex",
                "--project-root",
                str(project_root),
                "--runtime-state-file",
                str(state_path),
                "--payload-file",
                str(confirmed_pending_path),
            ],
        )
        checks["pendingReviewRejected"] = pending.returncode != 0
        details["pendingReviewOutput"] = (pending.stderr or pending.stdout).strip()

        write_json(
            state_path,
            {
                "status": "summarizing",
                "entry_type": "mistake",
                "mode": "normal",
                "case_id": "archive-contract-case",
                "host": "codex",
                "project_root": str(project_root),
            },
        )
        confirmed = run_python_raw(
            root,
            CLI_SCRIPT,
            [
                "archive",
                "--host",
                "codex",
                "--project-root",
                str(project_root),
                "--runtime-state-file",
                str(state_path),
                "--payload-file",
                str(confirmed_pending_path),
            ],
        )
        checks["confirmedAccepted"] = confirmed.returncode == 0
        details["confirmedOutput"] = (confirmed.stderr or confirmed.stdout).strip()

    failures = [{"check": key, "details": details.get(f"{key}Output", "")} for key, ok in checks.items() if not ok]
    violation_count = len(failures)
    return result(
        name="archive_contract",
        passed=violation_count == 0,
        score=1.0 if violation_count == 0 else 0.0,
        checks=checks,
        violationCount=violation_count,
        failures=failures,
    )


def seed_retrieval_store(root: Path, project_root: Path) -> None:
    entries = [
        {
            "entryType": "mistake",
            "caseId": "implementation-case",
            "title": "read implementation first",
            "summary": "read source code before updating docs",
            "userConfirmed": True,
            "scopeDecision": "project",
            "keywords": ["implementation", "docs"],
            "rules": ["read implementation before docs"],
            "confirmedUnderstanding": ["source code is the authority"],
            "originalPrompt": "update docs",
            "correctionFeedback": "you did not inspect implementation",
            "finalReply": "checked implementation before editing docs",
            "memoryPriority": 3.0,
            "retrievalCount": 3,
            "hitCount": 2,
        },
        {
            "entryType": "note",
            "caseId": "cache-case",
            "title": "refresh memory cache",
            "summary": "refresh memory after archive",
            "userConfirmed": True,
            "scopeDecision": "project",
            "keywords": ["memory", "cache"],
            "rules": ["refresh memory after archive"],
            "confirmedUnderstanding": ["cache follows archive"],
            "noteReason": "long-lived cache rule",
            "noteContent": ["refresh memory cache after writes"],
        },
    ]
    for index, entry in enumerate(entries):
        payload_path = project_root / f"retrieval-{index}.json"
        write_json(payload_path, entry)
        completed = run_python_raw(
            root,
            CLI_SCRIPT,
            [
                "archive",
                "--host",
                "codex",
                "--project-root",
                str(project_root),
                "--payload-file",
                str(payload_path),
            ],
        )
        if completed.returncode != 0:
            raise RuntimeError((completed.stderr or completed.stdout).strip())


def rank_for_case(results: list[dict[str, Any]], expected_case_id: str) -> int | None:
    for index, item in enumerate(results, start=1):
        if item.get("caseId") == expected_case_id:
            return index
    return None


def evaluate_retrieval_quality(root: Path, min_top1: float) -> dict[str, Any]:
    expected_case_id = "implementation-case"
    query_text = "read implementation before updating docs"
    checks: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        seed_retrieval_store(root, project_root)

        query_output = run_python(
            root,
            CLI_SCRIPT,
            [
                "query",
                "--host",
                "codex",
                "--project-root",
                str(project_root),
                "--scope",
                "project",
                "--text",
                query_text,
                "--limit",
                "3",
            ],
        )
        checks.append({"name": "query", "rank": rank_for_case(query_output.get("results", []), expected_case_id)})

        scholar_output = run_python(
            root,
            CLI_SCRIPT,
            [
                "scholar",
                "--host",
                "codex",
                "--project-root",
                str(project_root),
                "--scope",
                "project",
                "--text",
                query_text,
                "--limit",
                "3",
            ],
        )
        checks.append({"name": "scholar", "rank": rank_for_case(scholar_output.get("results", []), expected_case_id)})

        context_output = run_python(
            root,
            CLI_SCRIPT,
            [
                "context",
                "--host",
                "codex",
                "--project-root",
                str(project_root),
                "--scope",
                "project",
                "--query",
                query_text,
                "--limit",
                "3",
            ],
        )
        evidence = context_output.get("project", {}).get("evidencePacket", {})
        matched_ids = evidence.get("matchedCaseIds") or []
        context_rank = matched_ids.index(expected_case_id) + 1 if expected_case_id in matched_ids else None
        checks.append({"name": "context", "rank": context_rank})

    top1_hits = sum(1 for check in checks if check["rank"] == 1)
    top1_accuracy = top1_hits / len(checks)
    reciprocal_ranks = [(1.0 / check["rank"]) if check["rank"] else 0.0 for check in checks]
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
    failures = [check for check in checks if check["rank"] != 1]
    return result(
        name="retrieval_quality",
        passed=top1_accuracy >= min_top1 and not failures,
        score=top1_accuracy,
        expectedCaseId=expected_case_id,
        checks=checks,
        top1Accuracy=round(top1_accuracy, 6),
        mrr=round(mrr, 6),
        minTop1Accuracy=min_top1,
        failures=failures,
    )


def evaluate_compact_recovery(root: Path, min_recovery: float) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as home_dir, tempfile.TemporaryDirectory() as project_dir:
        home = Path(home_dir)
        state_path = home / ".mistakebook" / "runtime-state.json"
        summary_path = home / "compact-summary.md"
        write_json(
            state_path,
            {
                "status": "pending_review",
                "entry_type": "mistake",
                "mode": "normal",
                "host": "codex",
                "project_root": project_dir,
                "case_id": "compact-case",
                "rejection_count": 1,
                "correction_attempt_count": 2,
            },
        )
        summary_path.write_text("Compact summary preserved compact-case and pending_review.", encoding="utf-8")
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        run_python(
            root,
            LIFECYCLE_SCRIPT,
            ["pre-compact", "--state-file", str(state_path)],
            env=env,
        )
        post_output = run_python(
            root,
            LIFECYCLE_SCRIPT,
            ["post-compact", "--compact-summary-file", str(summary_path)],
            env=env,
        )
        journal_path = home / ".mistakebook" / "runtime-journal.md"
        journal = journal_path.read_text(encoding="utf-8") if journal_path.exists() else ""

    checks = {
        "activeCaseSurvived": bool(post_output.get("activeCaseSurvived")),
        "journalRefreshed": "## Compact Summary" in journal,
        "caseIdRestored": "compact-case" in post_output["hookSpecificOutput"]["additionalContext"],
    }
    passed_count = sum(1 for ok in checks.values() if ok)
    recovery_rate = passed_count / len(checks)
    failures = [{"check": key} for key, ok in checks.items() if not ok]
    return result(
        name="compact_recovery",
        passed=recovery_rate >= min_recovery and not failures,
        score=recovery_rate,
        checks=checks,
        recoveryPassRate=round(recovery_rate, 6),
        minRecoveryPassRate=min_recovery,
        failures=failures,
    )


def file_contains(root: Path, relative_path: str, required_terms: list[str]) -> tuple[bool, list[str]]:
    path = root / relative_path
    if not path.exists():
        return False, [f"missing:{relative_path}"]
    text = path.read_text(encoding="utf-8-sig")
    missing = [term for term in required_terms if term not in text]
    return not missing, missing


def evaluate_cross_host(root: Path) -> dict[str, Any]:
    host_checks = {
        "codex": [
            ("codex/mistakebook/SKILL.md", ["scripts/lifecycle_hooks.py", "scripts/trigger_report.py"]),
            ("codex/scholar/SKILL.md", ["scholar"]),
            (".codex/INSTALL.md", ["$mistakebook", "$scholar"]),
        ],
        "claude": [
            ("hooks/hooks.json", ["UserPromptSubmit", "PreCompact", "PostCompact", "SubagentStart", "SessionEnd"]),
            ("hooks/correction-trigger.sh", ["trigger_report.py", "correction"]),
            ("hooks/lifecycle-post-compact.sh", ["lifecycle_hooks.py", "post-compact"]),
        ],
        "vscode": [
            ("vscode/copilot-instructions.md", ["mistakebook"]),
            ("vscode/instructions/mistakebook.instructions.md", ["mistakebook"]),
            ("vscode/prompts/scholar.prompt.md", ["scholar"]),
        ],
    }
    matrix: dict[str, Any] = {}
    compatible_hosts: list[str] = []
    failures: list[dict[str, Any]] = []

    for host, checks in host_checks.items():
        host_failures: list[dict[str, Any]] = []
        for relative_path, required_terms in checks:
            ok, missing = file_contains(root, relative_path, required_terms)
            if not ok:
                host_failures.append({"file": relative_path, "missing": missing})
        matrix[host] = {"passed": not host_failures, "failures": host_failures}
        if host_failures:
            failures.append({"host": host, "failures": host_failures})
        else:
            compatible_hosts.append(host)

    return result(
        name="cross_host",
        passed=not failures,
        score=len(compatible_hosts) / len(host_checks),
        compatibleHosts=compatible_hosts,
        matrix=matrix,
        failures=failures,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Mistakebook behavioral eval suites.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON only.")
    parser.add_argument("--suite", action="append", choices=SUITES, help="Run only the selected suite. Can repeat.")
    parser.add_argument("--min-trigger-recall", type=float, default=1.0)
    parser.add_argument("--max-trigger-false-positive-rate", type=float, default=0.0)
    parser.add_argument("--min-retrieval-top1", type=float, default=1.0)
    parser.add_argument("--min-compact-recovery", type=float, default=1.0)
    return parser


def run_suites(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    selected = tuple(args.suite) if args.suite else SUITES
    suite_results: dict[str, dict[str, Any]] = {}

    if "trigger_recall" in selected:
        suite_results["trigger_recall"] = evaluate_trigger_recall(root, args.min_trigger_recall)
    if "trigger_precision" in selected:
        suite_results["trigger_precision"] = evaluate_trigger_precision(root, args.max_trigger_false_positive_rate)
    if "archive_contract" in selected:
        suite_results["archive_contract"] = evaluate_archive_contract(root)
    if "retrieval_quality" in selected:
        suite_results["retrieval_quality"] = evaluate_retrieval_quality(root, args.min_retrieval_top1)
    if "compact_recovery" in selected:
        suite_results["compact_recovery"] = evaluate_compact_recovery(root, args.min_compact_recovery)
    if "cross_host" in selected:
        suite_results["cross_host"] = evaluate_cross_host(root)

    failed_suites = [name for name, payload in suite_results.items() if not payload["passed"]]
    return {
        "overall": {
            "passed": not failed_suites,
            "failedSuites": failed_suites,
            "suiteCount": len(suite_results),
        },
        "suites": suite_results,
    }


def render_text_report(report: dict[str, Any]) -> str:
    lines = [
        "Mistakebook Eval Harness",
        f"overall: {'PASS' if report['overall']['passed'] else 'FAIL'}",
        f"failed_suites: {', '.join(report['overall']['failedSuites']) or 'none'}",
        "",
        "Suites:",
    ]
    for name, payload in report["suites"].items():
        lines.append(f"- {name}: {'PASS' if payload['passed'] else 'FAIL'} score={payload.get('score', 'n/a')}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = run_suites(args)
    if args.json:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        print(render_text_report(report))
    return 0 if report["overall"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
