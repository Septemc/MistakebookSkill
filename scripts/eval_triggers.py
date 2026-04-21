#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


EXPECTED_GROUPS = {
    "should-trigger.txt": "trigger",
    "should-trigger-ascended.txt": "ascended",
    "should-not-trigger.txt": "none",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Mistakebook trigger matchers against sample prompts.")
    parser.add_argument("--root", default=".", help="Repository root containing hooks/ and evals/ directories.")
    return parser.parse_args(argv)


def load_matchers(root: Path) -> tuple[re.Pattern[str], re.Pattern[str]]:
    hooks_path = root / "hooks" / "hooks.json"
    with hooks_path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    user_prompt_hooks = payload["hooks"]["UserPromptSubmit"]
    correction_matcher = re.compile(user_prompt_hooks[0]["matcher"])
    ascended_matcher = re.compile(user_prompt_hooks[1]["matcher"])
    return correction_matcher, ascended_matcher


def load_samples(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def classify_sample(sample: str, correction_matcher: re.Pattern[str], ascended_matcher: re.Pattern[str]) -> str:
    if ascended_matcher.search(sample):
        return "ascended"
    if correction_matcher.search(sample):
        return "correction"
    return "none"


def is_expected_match(expected: str, actual: str) -> bool:
    if expected == "trigger":
        return actual in {"correction", "ascended"}
    return expected == actual


def evaluate_group(
    file_name: str,
    expected: str,
    samples: list[str],
    correction_matcher: re.Pattern[str],
    ascended_matcher: re.Pattern[str],
) -> dict[str, Any]:
    failures: list[dict[str, str]] = []
    passed = 0

    for sample in samples:
        actual = classify_sample(sample, correction_matcher, ascended_matcher)
        if is_expected_match(expected, actual):
            passed += 1
            continue
        failures.append({"sample": sample, "expected": expected, "actual": actual})

    return {
        "file_name": file_name,
        "expected": expected,
        "total": len(samples),
        "passed": passed,
        "failed": len(failures),
        "failures": failures,
    }


def render_group_summary(group: dict[str, Any]) -> list[str]:
    lines = [
        f"{group['file_name']}: total={group['total']} passed={group['passed']} failed={group['failed']} expected={group['expected']}"
    ]
    for failure in group["failures"]:
        lines.append(
            f"  - expected={failure['expected']} actual={failure['actual']} sample={failure['sample']}"
        )
    return lines


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    correction_matcher, ascended_matcher = load_matchers(root)

    print("Loaded matchers:")
    print(f"- correction: {correction_matcher.pattern}")
    print(f"- ascended: {ascended_matcher.pattern}")

    groups: list[dict[str, Any]] = []
    eval_dir = root / "evals" / "trigger-prompts"
    for file_name, expected in EXPECTED_GROUPS.items():
        path = eval_dir / file_name
        samples = load_samples(path)
        group = evaluate_group(file_name, expected, samples, correction_matcher, ascended_matcher)
        groups.append(group)

    print()
    print("Results:")
    for group in groups:
        for line in render_group_summary(group):
            print(line)

    trigger_group = next(group for group in groups if group["file_name"] == "should-trigger.txt")
    ascended_group = next(group for group in groups if group["file_name"] == "should-trigger-ascended.txt")
    negative_group = next(group for group in groups if group["file_name"] == "should-not-trigger.txt")
    total_samples = sum(group["total"] for group in groups)
    total_passed = sum(group["passed"] for group in groups)
    overall_pass = all(group["failed"] == 0 for group in groups)

    print()
    print("Summary:")
    print(f"- trigger recall: {trigger_group['passed']}/{trigger_group['total']}")
    print(f"- ascended recall: {ascended_group['passed']}/{ascended_group['total']}")
    print(f"- negative set pass rate: {negative_group['passed']}/{negative_group['total']}")
    print(f"- overall: {'PASS' if overall_pass else 'FAIL'} ({total_passed}/{total_samples})")

    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
