import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "scripts" / "mistakebook_cli.py"


class MistakebookCliScholarTests(unittest.TestCase):
    def run_cli(self, *args: str, home_dir: str | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if home_dir:
            env["HOME"] = home_dir
            env["USERPROFILE"] = home_dir
        return subprocess.run(
            [sys.executable, str(CLI_PATH), *args],
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
            env=env,
        )

    def archive_entry(self, project_root: str, payload: dict[str, object], home_dir: str) -> None:
        result = self.run_cli(
            "archive",
            "--host",
            "codex",
            "--project-root",
            project_root,
            "--payload",
            json.dumps(payload, ensure_ascii=False),
            home_dir=home_dir,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

    def test_scholar_returns_single_line_hint_for_high_confidence_match(self) -> None:
        with tempfile.TemporaryDirectory() as project_root, tempfile.TemporaryDirectory() as home_dir:
            self.archive_entry(
                project_root,
                {
                    "entryType": "mistake",
                    "title": "verify-real-implementation",
                    "summary": "read the implementation before updating docs",
                    "scopeDecision": "project",
                    "keywords": ["implementation", "docs"],
                    "rules": ["read implementation before docs"],
                    "confirmedUnderstanding": ["implementation first"],
                    "memoryPriority": 3.0,
                    "retrievalCount": 4,
                    "hitCount": 3,
                },
                home_dir,
            )
            self.archive_entry(
                project_root,
                {
                    "entryType": "mistake",
                    "title": "refresh-memory-after-write",
                    "summary": "refresh memory files after editing entries",
                    "scopeDecision": "project",
                    "keywords": ["memory"],
                    "rules": ["refresh memory after edits"],
                    "confirmedUnderstanding": ["memory refresh matters"],
                    "memoryPriority": 1.0,
                },
                home_dir,
            )

            result = self.run_cli(
                "scholar",
                "--host",
                "codex",
                "--project-root",
                project_root,
                "--text",
                "read implementation before updating docs",
                "--limit",
                "3",
                home_dir=home_dir,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            self.assertTrue(output["enabled"])
            self.assertTrue(output["shouldInject"])
            self.assertEqual(output["confidence"], "high")
            self.assertIn("verify-real-implementation", output["message"])
            self.assertNotIn("\n", output["message"])
            self.assertEqual(len(output["matchedCaseIds"]), 1)
            self.assertTrue(output["results"])

            catalog_path = Path(project_root) / ".mistakebook" / "state" / "catalog.json"
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            counts = {entry["title"]: entry.get("retrievalCount", 0) for entry in catalog}
            self.assertEqual(counts["verify-real-implementation"], 4)
            self.assertEqual(counts["refresh-memory-after-write"], 0)

    def test_scholar_stays_silent_in_ascended_phase(self) -> None:
        with tempfile.TemporaryDirectory() as project_root, tempfile.TemporaryDirectory() as home_dir:
            self.archive_entry(
                project_root,
                {
                    "entryType": "mistake",
                    "title": "verify-real-implementation",
                    "summary": "read the implementation before updating docs",
                    "scopeDecision": "project",
                    "keywords": ["implementation", "docs"],
                    "rules": ["read implementation before docs"],
                    "confirmedUnderstanding": ["implementation first"],
                    "memoryPriority": 3.0,
                },
                home_dir,
            )

            result = self.run_cli(
                "scholar",
                "--host",
                "codex",
                "--project-root",
                project_root,
                "--text",
                "read implementation before updating docs",
                "--phase",
                "ascended",
                home_dir=home_dir,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            self.assertTrue(output["enabled"])
            self.assertFalse(output["shouldInject"])
            self.assertEqual(output["reason"], "phase_blocked")
            self.assertEqual(output["message"], "")

    def test_scholar_respects_disabled_config(self) -> None:
        with tempfile.TemporaryDirectory() as project_root, tempfile.TemporaryDirectory() as home_dir:
            self.archive_entry(
                project_root,
                {
                    "entryType": "mistake",
                    "title": "verify-real-implementation",
                    "summary": "read the implementation before updating docs",
                    "scopeDecision": "project",
                    "keywords": ["implementation", "docs"],
                    "rules": ["read implementation before docs"],
                    "confirmedUnderstanding": ["implementation first"],
                    "memoryPriority": 3.0,
                },
                home_dir,
            )
            config_result = self.run_cli(
                "config",
                "--scholar",
                "off",
                home_dir=home_dir,
            )
            self.assertEqual(config_result.returncode, 0, msg=config_result.stderr or config_result.stdout)

            result = self.run_cli(
                "scholar",
                "--host",
                "codex",
                "--project-root",
                project_root,
                "--text",
                "read implementation before updating docs",
                home_dir=home_dir,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            self.assertFalse(output["enabled"])
            self.assertFalse(output["shouldInject"])
            self.assertEqual(output["reason"], "disabled")
            self.assertEqual(output["message"], "")

    def test_config_can_toggle_scholar_without_breaking_auto_detect(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir:
            auto_detect_result = self.run_cli(
                "config",
                "--auto-detect",
                "off",
                home_dir=home_dir,
            )
            self.assertEqual(auto_detect_result.returncode, 0, msg=auto_detect_result.stderr or auto_detect_result.stdout)
            auto_detect_output = json.loads(auto_detect_result.stdout)
            self.assertFalse(auto_detect_output["auto_detect"])
            self.assertTrue(auto_detect_output["scholar"])

            scholar_result = self.run_cli(
                "config",
                "--scholar",
                "off",
                home_dir=home_dir,
            )
            self.assertEqual(scholar_result.returncode, 0, msg=scholar_result.stderr or scholar_result.stdout)
            scholar_output = json.loads(scholar_result.stdout)
            self.assertFalse(scholar_output["auto_detect"])
            self.assertFalse(scholar_output["scholar"])

            status_result = self.run_cli(
                "status",
                "--host",
                "codex",
                "--project-root",
                ".",
                "--scope",
                "project",
                home_dir=home_dir,
            )
            self.assertEqual(status_result.returncode, 0, msg=status_result.stderr or status_result.stdout)
            status_output = json.loads(status_result.stdout)
            self.assertFalse(status_output["config"]["auto_detect"])
            self.assertFalse(status_output["config"]["scholar"])


if __name__ == "__main__":
    unittest.main()
