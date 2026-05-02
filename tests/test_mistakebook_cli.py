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
            "userConfirmed": True,
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
            "userConfirmed": True,
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
            "userConfirmed": True,
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
            "userConfirmed": True,
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

    def test_archive_preserves_chinese_text_in_generated_markdown(self) -> None:
        payload = {
            "entryType": "mistake",
            "caseId": "utf8-chinese-case",
            "title": "中文文档不应乱码",
            "summary": "写入 PROJECT_MEMORY.md 时必须保留中文。",
            "userConfirmed": True,
            "scopeDecision": "project",
            "scopeReasoning": ["项目级规则"],
            "keywords": ["中文", "文档", "编码"],
            "rules": ["写文档必须使用 UTF-8 编码"],
            "confirmedUnderstanding": ["当前版本需要防止问号乱码"],
            "whatWentWrong": ["旧版本曾把中文写成连续问号"],
            "preventionChecklist": ["生成后检查 PROJECT_MEMORY.md"],
            "originalPrompt": "朋友反馈之前版本写文档会乱码",
            "correctionFeedback": "确认当前版本是否还会乱码",
            "finalReply": "用真实归档流程生成中文 Markdown 并验证",
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
            case_path = Path(output["project"]["case_path"])
            memory_path = Path(tmpdir) / ".mistakebook" / "memory" / "PROJECT_MEMORY.md"
            index_path = Path(tmpdir) / ".mistakebook" / "failures" / "INDEX.md"

            combined = "\n".join(
                [
                    case_path.read_text(encoding="utf-8"),
                    memory_path.read_text(encoding="utf-8"),
                    index_path.read_text(encoding="utf-8"),
                ]
            )
            self.assertIn("中文文档不应乱码", combined)
            self.assertIn("写文档必须使用 UTF-8 编码", combined)
            self.assertIn("当前版本需要防止问号乱码", combined)
            self.assertNotIn("\ufffd", combined)
            self.assertNotRegex(combined, r"\?{4,}")

    def test_archive_rejects_likely_encoding_corruption_before_writing(self) -> None:
        payload = {
            "entryType": "mistake",
            "caseId": "corrupt-text-case",
            "title": "?" * 6,
            "summary": "?" * 12,
            "userConfirmed": True,
            "scopeDecision": "project",
            "rules": ["?" * 8],
            "confirmedUnderstanding": ["encoding corruption must not be archived"],
            "originalPrompt": "raw Chinese was corrupted before reaching the CLI",
            "correctionFeedback": "reject question-mark runs",
            "finalReply": "do not write corrupted memory",
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

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("likely encoding corruption", result.stderr or result.stdout)
            catalog_path = Path(tmpdir) / ".mistakebook" / "state" / "catalog.json"
            self.assertFalse(catalog_path.exists())

    def test_archive_rejects_payload_without_user_confirmation(self) -> None:
        payload = {
            "entryType": "mistake",
            "title": "unconfirmed archive",
            "summary": "archive should require explicit confirmation",
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
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("payload must set userConfirmed=true before archive", result.stderr or result.stdout)

    def test_archive_runtime_state_moves_from_summarizing_to_archived(self) -> None:
        payload = {
            "entryType": "mistake",
            "caseId": "runtime-case",
            "title": "runtime state archive",
            "summary": "archive should close the runtime state",
            "userConfirmed": True,
            "scopeDecision": "project",
            "scopeReasoning": ["runtime state is project-local"],
            "rules": ["archive only after summarizing"],
            "confirmedUnderstanding": ["runtime state reached summarizing"],
            "originalPrompt": "user prompt",
            "correctionFeedback": "user correction",
            "finalReply": "fixed reply",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "runtime_state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "status": "summarizing",
                        "entry_type": "mistake",
                        "mode": "normal",
                        "case_id": "runtime-case",
                        "host": "codex",
                        "project_root": tmpdir,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            result = self.run_cli(
                "archive",
                "--host",
                "codex",
                "--project-root",
                tmpdir,
                "--runtime-state-file",
                str(state_path),
                "--payload",
                json.dumps(payload, ensure_ascii=False),
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["status"], "archived")
            self.assertEqual(state["case_id"], "runtime-case")
            self.assertEqual(state["archived_entry_type"], "mistake")

    def test_archive_runtime_state_rejects_case_mismatch_before_writing(self) -> None:
        payload = {
            "entryType": "mistake",
            "caseId": "other-case",
            "title": "runtime state archive",
            "summary": "archive should reject mismatched runtime case",
            "userConfirmed": True,
            "scopeDecision": "project",
            "scopeReasoning": ["runtime state is project-local"],
            "rules": ["archive only the active case"],
            "confirmedUnderstanding": ["runtime state reached summarizing"],
            "originalPrompt": "user prompt",
            "correctionFeedback": "user correction",
            "finalReply": "fixed reply",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "runtime_state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "status": "summarizing",
                        "entry_type": "mistake",
                        "mode": "normal",
                        "case_id": "runtime-case",
                        "host": "codex",
                        "project_root": tmpdir,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            result = self.run_cli(
                "archive",
                "--host",
                "codex",
                "--project-root",
                tmpdir,
                "--runtime-state-file",
                str(state_path),
                "--payload",
                json.dumps(payload, ensure_ascii=False),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("archive case_id mismatch", result.stderr or result.stdout)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["status"], "summarizing")
            catalog_path = Path(tmpdir) / ".mistakebook" / "state" / "catalog.json"
            self.assertFalse(catalog_path.exists())

    def test_archive_records_user_confirmation_in_catalog(self) -> None:
        payload = {
            "entryType": "mistake",
            "title": "confirmed archive",
            "summary": "catalog should preserve confirmation evidence",
            "userConfirmed": True,
            "scopeDecision": "project",
            "scopeReasoning": ["confirmed by user"],
            "rules": ["archive only after confirmation"],
            "confirmedUnderstanding": ["confirmation is part of provenance"],
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
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            catalog_path = Path(tmpdir) / ".mistakebook" / "state" / "catalog.json"
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            self.assertTrue(catalog[0]["userConfirmed"])


if __name__ == "__main__":
    unittest.main()
