import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "scripts" / "mistakebook_cli.py"
LIFECYCLE_PATH = REPO_ROOT / "scripts" / "lifecycle_hooks.py"
HOOKS_PATH = REPO_ROOT / "hooks" / "hooks.json"


class LifecycleHookTests(unittest.TestCase):
    def run_lifecycle(
        self,
        *args: str,
        home_dir: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if home_dir:
            env["HOME"] = home_dir
            env["USERPROFILE"] = home_dir
        env.setdefault("PYTHONIOENCODING", "utf-8")
        return subprocess.run(
            [sys.executable, str(LIFECYCLE_PATH), *args],
            text=True,
            encoding="utf-8",
            capture_output=True,
            cwd=REPO_ROOT,
            env=env,
        )

    def run_cli(
        self,
        *args: str,
        home_dir: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if home_dir:
            env["HOME"] = home_dir
            env["USERPROFILE"] = home_dir
        env.setdefault("PYTHONIOENCODING", "utf-8")
        return subprocess.run(
            [sys.executable, str(CLI_PATH), *args],
            text=True,
            encoding="utf-8",
            capture_output=True,
            cwd=REPO_ROOT,
            env=env,
        )

    def write_state(self, path: Path, **updates: object) -> None:
        state = {
            "status": "pending_review",
            "entry_type": "mistake",
            "mode": "normal",
            "host": "codex",
            "project_root": "E:/repo",
            "case_id": "lifecycle-case",
            "rejection_count": 1,
            "correction_attempt_count": 2,
        }
        state.update(updates)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    def archive_entry(self, project_root: str, payload: dict[str, object], home_dir: str) -> None:
        payload = dict(payload)
        payload.setdefault("userConfirmed", True)
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

    def test_pre_and_post_compact_round_trip_runtime_journal(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir:
            state_path = Path(home_dir) / ".mistakebook" / "runtime-state.json"
            self.write_state(state_path)

            pre = self.run_lifecycle("pre-compact", "--state-file", str(state_path), home_dir=home_dir)
            self.assertEqual(pre.returncode, 0, msg=pre.stderr or pre.stdout)
            pre_output = json.loads(pre.stdout)
            self.assertEqual(pre_output["hookSpecificOutput"]["hookEventName"], "PreCompact")

            journal_path = Path(home_dir) / ".mistakebook" / "runtime-journal.md"
            self.assertTrue(journal_path.exists())
            journal = journal_path.read_text(encoding="utf-8")
            self.assertIn("case_id: lifecycle-case", journal)
            self.assertIn("status: pending_review", journal)

            post = self.run_lifecycle("post-compact", home_dir=home_dir)
            self.assertEqual(post.returncode, 0, msg=post.stderr or post.stdout)
            post_output = json.loads(post.stdout)
            context = post_output["hookSpecificOutput"]["additionalContext"]
            self.assertEqual(post_output["hookSpecificOutput"]["hookEventName"], "PostCompact")
            self.assertIn("lifecycle-case", context)
            self.assertIn("Do not archive", context)

    def test_post_compact_reads_summary_and_refreshes_runtime_journal(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir:
            state_path = Path(home_dir) / ".mistakebook" / "runtime-state.json"
            self.write_state(state_path)
            summary_path = Path(home_dir) / "compact-summary.md"
            summary_path.write_text(
                "Compact summary preserved lifecycle-case and the pending_review state.",
                encoding="utf-8",
            )

            pre = self.run_lifecycle("pre-compact", "--state-file", str(state_path), home_dir=home_dir)
            self.assertEqual(pre.returncode, 0, msg=pre.stderr or pre.stdout)

            post = self.run_lifecycle(
                "post-compact",
                "--compact-summary-file",
                str(summary_path),
                home_dir=home_dir,
            )

            self.assertEqual(post.returncode, 0, msg=post.stderr or post.stdout)
            post_output = json.loads(post.stdout)
            context = post_output["hookSpecificOutput"]["additionalContext"]
            self.assertTrue(post_output["activeCaseSurvived"])
            self.assertIn("Recovery check: active case survived compact summary.", context)

            journal = (Path(home_dir) / ".mistakebook" / "runtime-journal.md").read_text(encoding="utf-8")
            self.assertIn("## Compact Summary", journal)
            self.assertIn("preserved lifecycle-case", journal)

    def test_post_compact_outputs_json_when_summary_has_utf8_bom(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir:
            state_path = Path(home_dir) / ".mistakebook" / "runtime-state.json"
            self.write_state(state_path)
            summary_path = Path(home_dir) / "compact-summary.md"
            summary_path.write_text(
                "Compact summary preserved lifecycle-case.",
                encoding="utf-8-sig",
            )

            pre = self.run_lifecycle("pre-compact", "--state-file", str(state_path), home_dir=home_dir)
            self.assertEqual(pre.returncode, 0, msg=pre.stderr or pre.stdout)

            post = self.run_lifecycle(
                "post-compact",
                "--compact-summary-file",
                str(summary_path),
                home_dir=home_dir,
            )

            self.assertEqual(post.returncode, 0, msg=post.stderr or post.stdout)
            post_output = json.loads(post.stdout)
            self.assertTrue(post_output["activeCaseSurvived"])

    def test_session_end_warns_and_saves_unfinished_case(self) -> None:
        with tempfile.TemporaryDirectory() as home_dir:
            state_path = Path(home_dir) / ".mistakebook" / "runtime-state.json"
            self.write_state(state_path, status="summarizing")

            result = self.run_lifecycle("session-end", "--state-file", str(state_path), home_dir=home_dir)

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            context = output["hookSpecificOutput"]["additionalContext"]
            self.assertIn("pending archive is unconfirmed", context)
            self.assertIn("lifecycle-case", context)
            self.assertTrue((Path(home_dir) / ".mistakebook" / "runtime-journal.md").exists())

    def test_subagent_start_injects_high_confidence_project_memory(self) -> None:
        with tempfile.TemporaryDirectory() as project_root, tempfile.TemporaryDirectory() as home_dir:
            self.archive_entry(
                project_root,
                {
                    "entryType": "mistake",
                    "caseId": "implementation-case",
                    "title": "read implementation first",
                    "summary": "read source code before updating docs",
                    "scopeDecision": "project",
                    "keywords": ["implementation", "docs"],
                    "rules": ["read implementation before docs"],
                    "confirmedUnderstanding": ["source code is the authority"],
                    "memoryPriority": 3.0,
                    "retrievalCount": 3,
                    "hitCount": 2,
                },
                home_dir,
            )

            result = self.run_lifecycle(
                "subagent-start",
                "--host",
                "codex",
                "--project-root",
                project_root,
                "--task-text",
                "read implementation before updating docs",
                home_dir=home_dir,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            context = output["hookSpecificOutput"]["additionalContext"]
            self.assertIn("implementation-case", context)
            self.assertIn("confidence=high", context)
            self.assertIn("read implementation first", context)

    def test_subagent_start_handles_utf8_cli_output(self) -> None:
        with tempfile.TemporaryDirectory() as project_root, tempfile.TemporaryDirectory() as home_dir:
            self.archive_entry(
                project_root,
                {
                    "entryType": "mistake",
                    "caseId": "utf8-subagent-case",
                    "title": "中文文档不应乱码",
                    "summary": "写中文文档时必须保持 UTF-8。",
                    "scopeDecision": "project",
                    "keywords": ["中文", "文档", "编码"],
                    "rules": ["写入文档必须保持 UTF-8"],
                    "confirmedUnderstanding": ["生命周期 hook 需要正确读取 UTF-8 CLI 输出"],
                },
                home_dir,
            )

            result = self.run_lifecycle(
                "subagent-start",
                "--host",
                "codex",
                "--project-root",
                project_root,
                "--scope",
                "project",
                "--task-text",
                "写中文文档并避免乱码",
                home_dir=home_dir,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            context = output["hookSpecificOutput"]["additionalContext"]
            self.assertIn("utf8-subagent-case", context)
            self.assertIn("中文文档不应乱码", context)

    def test_subagent_stop_records_hit_metrics_for_case_ids(self) -> None:
        with tempfile.TemporaryDirectory() as project_root, tempfile.TemporaryDirectory() as home_dir:
            self.archive_entry(
                project_root,
                {
                    "entryType": "mistake",
                    "caseId": "implementation-case",
                    "title": "read implementation first",
                    "summary": "read source code before updating docs",
                    "scopeDecision": "project",
                    "keywords": ["implementation"],
                    "rules": ["read implementation before docs"],
                    "confirmedUnderstanding": ["source code is the authority"],
                },
                home_dir,
            )

            result = self.run_lifecycle(
                "subagent-stop",
                "--host",
                "codex",
                "--project-root",
                project_root,
                "--case-id",
                "implementation-case",
                "--kind",
                "hit",
                home_dir=home_dir,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            self.assertEqual(output["updatedCount"], 1)
            catalog_path = Path(project_root) / ".mistakebook" / "state" / "catalog.json"
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            self.assertEqual(catalog[0]["hitCount"], 1)

    def test_hooks_json_wires_all_lifecycle_events_to_commands(self) -> None:
        hooks_payload = json.loads(HOOKS_PATH.read_text(encoding="utf-8"))
        expected_events = {
            "PreCompact": "lifecycle-pre-compact.sh",
            "PostCompact": "lifecycle-post-compact.sh",
            "SubagentStart": "lifecycle-subagent-start.sh",
            "SubagentStop": "lifecycle-subagent-stop.sh",
            "SessionEnd": "lifecycle-session-end.sh",
        }

        for event_name, script_name in expected_events.items():
            self.assertIn(event_name, hooks_payload["hooks"])
            event_hooks = hooks_payload["hooks"][event_name]
            commands = [
                hook.get("command", "")
                for entry in event_hooks
                for hook in entry.get("hooks", [])
                if hook.get("type") == "command"
            ]
            self.assertTrue(any(script_name in command for command in commands), msg=(event_name, commands))

    def test_lifecycle_wrapper_scripts_preserve_runtime_env_contract(self) -> None:
        pre_compact = (REPO_ROOT / "hooks" / "lifecycle-pre-compact.sh").read_text(encoding="utf-8")
        post_compact = (REPO_ROOT / "hooks" / "lifecycle-post-compact.sh").read_text(encoding="utf-8")
        session_end = (REPO_ROOT / "hooks" / "lifecycle-session-end.sh").read_text(encoding="utf-8")
        subagent_stop = (REPO_ROOT / "hooks" / "lifecycle-subagent-stop.sh").read_text(encoding="utf-8")

        self.assertIn("MISTAKEBOOK_RUNTIME_STATE_FILE", pre_compact)
        self.assertIn("MISTAKEBOOK_RUNTIME_JOURNAL_FILE", pre_compact)
        self.assertIn("MISTAKEBOOK_RUNTIME_JOURNAL_FILE", post_compact)
        self.assertIn("MISTAKEBOOK_COMPACT_SUMMARY_FILE", post_compact)
        self.assertIn("MISTAKEBOOK_RUNTIME_STATE_FILE", session_end)
        self.assertIn("MISTAKEBOOK_RUNTIME_JOURNAL_FILE", session_end)
        self.assertIn('--case-id "$CASE_IDS"', subagent_stop)


if __name__ == "__main__":
    unittest.main()
