import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = REPO_ROOT / "scripts" / "eval_harness.py"


class EvalHarnessTests(unittest.TestCase):
    def run_harness(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(HARNESS_PATH), "--root", str(REPO_ROOT), "--json", *args],
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
        )

    def test_eval_harness_outputs_json_report_for_all_core_suites(self) -> None:
        result = self.run_harness()

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        output = json.loads(result.stdout)
        self.assertTrue(output["overall"]["passed"])
        self.assertEqual(output["overall"]["failedSuites"], [])

        suites = output["suites"]
        self.assertEqual(
            set(suites),
            {
                "trigger_recall",
                "trigger_precision",
                "archive_contract",
                "retrieval_quality",
                "compact_recovery",
                "cross_host",
            },
        )
        self.assertEqual(suites["trigger_recall"]["score"], 1.0)
        self.assertEqual(suites["trigger_precision"]["falsePositiveRate"], 0.0)
        self.assertEqual(suites["archive_contract"]["violationCount"], 0)
        self.assertEqual(suites["retrieval_quality"]["top1Accuracy"], 1.0)
        self.assertEqual(suites["retrieval_quality"]["mrr"], 1.0)
        self.assertEqual(suites["compact_recovery"]["recoveryPassRate"], 1.0)
        self.assertEqual(set(suites["cross_host"]["compatibleHosts"]), {"codex", "claude", "vscode"})

    def test_eval_harness_fails_when_threshold_is_unreachable(self) -> None:
        result = self.run_harness("--min-trigger-recall", "1.01")

        self.assertNotEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertFalse(output["overall"]["passed"])
        self.assertIn("trigger_recall", output["overall"]["failedSuites"])

    def test_eval_harness_can_run_one_suite(self) -> None:
        result = self.run_harness("--suite", "archive_contract")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        output = json.loads(result.stdout)
        self.assertTrue(output["overall"]["passed"])
        self.assertEqual(set(output["suites"]), {"archive_contract"})
        self.assertEqual(output["suites"]["archive_contract"]["violationCount"], 0)


if __name__ == "__main__":
    unittest.main()
