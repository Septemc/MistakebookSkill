import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TRIGGER_REPORT_PATH = REPO_ROOT / "scripts" / "trigger_report.py"


class TriggerReportTests(unittest.TestCase):
    def run_trigger(self, *args: str, home_dir: str | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if home_dir:
            env["HOME"] = home_dir
            env["USERPROFILE"] = home_dir
        return subprocess.run(
            [sys.executable, str(TRIGGER_REPORT_PATH), *args],
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
            env=env,
        )

    def test_correction_report_outputs_structured_user_prompt_context(self) -> None:
        result = self.run_trigger("correction")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(output["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertIn("[Mistakebook Trigger Report]", context)
        self.assertIn("triggerType=correction", context)
        self.assertIn("runtimeStatus=armed", context)
        self.assertIn("Do not archive", context)

    def test_ascended_report_outputs_structured_user_prompt_context(self) -> None:
        result = self.run_trigger("ascended")

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(output["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertIn("triggerType=ascended", context)
        self.assertIn("mode=ascended", context)
        self.assertIn("context --host codex", context)

    def test_scholar_preflight_respects_config_and_outputs_structured_context(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir:
            config_path = Path(home_dir) / ".mistakebook" / "config.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(json.dumps({"scholar": False}), encoding="utf-8")

            disabled = self.run_trigger("scholar-preflight", home_dir=home_dir)
            self.assertEqual(disabled.returncode, 0, msg=disabled.stderr or disabled.stdout)
            self.assertEqual(json.loads(disabled.stdout)["hookSpecificOutput"]["additionalContext"], "")

            config_path.write_text(json.dumps({"scholar": True}), encoding="utf-8")
            enabled = self.run_trigger("scholar-preflight", home_dir=home_dir)
            self.assertEqual(enabled.returncode, 0, msg=enabled.stderr or enabled.stdout)
            context = json.loads(enabled.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("[Mistakebook Scholar Preflight]", context)
            self.assertIn("python scripts/mistakebook_cli.py scholar --host claude", context)
            self.assertIn("shouldInject = true", context)


if __name__ == "__main__":
    unittest.main()
