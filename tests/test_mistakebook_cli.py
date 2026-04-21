import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "scripts" / "mistakebook_cli.py"


class MistakebookCliArchiveTests(unittest.TestCase):
    def run_cli(self, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI_PATH), *args],
            input=stdin,
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
        )

    def test_archive_accepts_payload_from_stdin(self) -> None:
        payload = {
            "entryType": "mistake",
            "title": "stdin archive",
            "summary": "archive payload should be accepted from stdin",
            "scopeDecision": "project",
            "scopeReasoning": ["project-local behavior"],
            "rules": ["prefer stdin for codex archive"],
            "confirmedUnderstanding": ["stdin should avoid temp json files"],
            "originalPrompt": "user prompt",
            "correctionFeedback": "user correction",
            "finalReply": "fixed reply",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_cli(
                "archive",
                "--host",
                "codex",
                "--project-root",
                tmpdir,
                "--payload-stdin",
                stdin=json.dumps(payload, ensure_ascii=False),
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            self.assertEqual(output["entryType"], "mistake")
            self.assertIn("project", output)
            case_path = Path(output["project"]["case_path"])
            self.assertTrue(case_path.exists(), msg=case_path)

    def test_archive_rejects_multiple_payload_sources(self) -> None:
        payload = {
            "entryType": "mistake",
            "title": "stdin archive",
            "summary": "archive payload should be accepted from stdin",
            "originalPrompt": "user prompt",
            "correctionFeedback": "user correction",
            "finalReply": "fixed reply",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_cli(
                "archive",
                "--host",
                "codex",
                "--project-root",
                tmpdir,
                "--payload",
                json.dumps(payload, ensure_ascii=False),
                "--payload-stdin",
                stdin=json.dumps(payload, ensure_ascii=False),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "archive accepts only one of --payload-file, --payload, or --payload-stdin",
                result.stderr or result.stdout,
            )

    def test_archive_rejects_empty_stdin_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_cli(
                "archive",
                "--host",
                "codex",
                "--project-root",
                tmpdir,
                "--payload-stdin",
                stdin="",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("archive received empty stdin payload", result.stderr or result.stdout)

    def test_archive_rejects_invalid_json_from_stdin(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_cli(
                "archive",
                "--host",
                "codex",
                "--project-root",
                tmpdir,
                "--payload-stdin",
                stdin="{invalid json}",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("archive failed to parse JSON from stdin", result.stderr or result.stdout)

    def test_archive_requires_exactly_one_payload_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_cli(
                "archive",
                "--host",
                "codex",
                "--project-root",
                tmpdir,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "archive requires exactly one of --payload-file, --payload, or --payload-stdin",
                result.stderr or result.stdout,
            )

    def test_archive_still_accepts_inline_payload(self) -> None:
        payload = {
            "entryType": "note",
            "title": "inline payload",
            "summary": "archive payload should still be accepted inline",
            "noteReason": "important reminder",
            "noteContent": ["keep inline payload working"],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.run_cli(
                "archive",
                "--host",
                "codex",
                "--project-root",
                tmpdir,
                "--payload",
                json.dumps(payload, ensure_ascii=False),
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            self.assertEqual(output["entryType"], "note")
            self.assertIn("project", output)

    def test_archive_still_accepts_payload_file(self) -> None:
        payload = {
            "entryType": "mistake",
            "title": "payload file",
            "summary": "archive payload should still be accepted from a file",
            "scopeDecision": "project",
            "scopeReasoning": ["project-local behavior"],
            "rules": ["keep payload-file working"],
            "confirmedUnderstanding": ["payload-file remains supported"],
            "originalPrompt": "user prompt",
            "correctionFeedback": "user correction",
            "finalReply": "fixed reply",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = Path(tmpdir) / "payload.json"
            payload_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = self.run_cli(
                "archive",
                "--host",
                "codex",
                "--project-root",
                tmpdir,
                "--payload-file",
                str(payload_path),
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            self.assertEqual(output["entryType"], "mistake")
            self.assertIn("project", output)


if __name__ == "__main__":
    unittest.main()
