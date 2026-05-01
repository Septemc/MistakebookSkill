import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "scripts" / "mistakebook_cli.py"


class MistakebookCliContextTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI_PATH), *args],
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
        )

    def archive_entry(self, project_root: str, payload: dict[str, object], global_root: str | None = None) -> dict[str, object]:
        args = [
            "archive",
            "--host",
            "codex",
            "--project-root",
            project_root,
            "--payload",
            json.dumps(payload, ensure_ascii=False),
        ]
        if global_root:
            args.extend(["--global-root", global_root])
        result = self.run_cli(*args)
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_context_without_query_keeps_full_export(self) -> None:
        with tempfile.TemporaryDirectory() as project_root:
            self.archive_entry(
                project_root,
                {
                    "entryType": "mistake",
                    "title": "先读真实实现",
                    "summary": "改文档前先核对真实实现",
                    "scopeDecision": "project",
                    "keywords": ["真实实现"],
                    "rules": ["先读真实实现再改文档"],
                    "confirmedUnderstanding": ["真实实现优先"],
                    "originalPrompt": "补文档",
                    "correctionFeedback": "你没有先读真实实现",
                    "finalReply": "已先核对实现",
                },
            )
            self.archive_entry(
                project_root,
                {
                    "entryType": "mistake",
                    "title": "缓存刷新不能漏",
                    "summary": "改完条目后记得刷新缓存",
                    "scopeDecision": "project",
                    "keywords": ["缓存"],
                    "rules": ["修改条目后刷新 memory"],
                    "confirmedUnderstanding": ["缓存和条目同步"],
                    "originalPrompt": "改缓存逻辑",
                    "correctionFeedback": "你忘了刷新缓存",
                    "finalReply": "已刷新缓存",
                },
            )
            self.archive_entry(
                project_root,
                {
                    "entryType": "note",
                    "title": "记住默认阈值",
                    "summary": "默认 memory threshold 是 12",
                    "scopeDecision": "project",
                    "noteReason": "长期配置约束",
                    "noteContent": ["memory threshold 默认是 12"],
                },
            )

            result = self.run_cli(
                "context",
                "--host",
                "codex",
                "--project-root",
                project_root,
                "--scope",
                "project",
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            project = output["project"]
            self.assertFalse(project["pruned"])
            self.assertEqual(project["totalEntries"], 3)
            self.assertEqual(project["returnedEntries"], 3)
            self.assertEqual(len(project["mistakes"]), 2)
            self.assertEqual(len(project["notes"]), 1)

    def test_context_query_returns_only_top_matches(self) -> None:
        with tempfile.TemporaryDirectory() as project_root:
            self.archive_entry(
                project_root,
                {
                    "entryType": "mistake",
                    "title": "先读真实实现",
                    "summary": "改文档前必须先核对真实实现和脚本输出",
                    "scopeDecision": "project",
                    "keywords": ["真实实现", "文档"],
                    "rules": ["先读真实实现再改文档"],
                    "confirmedUnderstanding": ["真实实现比猜测更重要"],
                    "originalPrompt": "更新说明文档",
                    "correctionFeedback": "你没有先核对真实实现",
                    "finalReply": "先检查实现再更新文档",
                    "memoryPriority": 3.0,
                },
            )
            self.archive_entry(
                project_root,
                {
                    "entryType": "mistake",
                    "title": "文档更新要贴近代码",
                    "summary": "文档更新不能脱离真实代码路径",
                    "scopeDecision": "project",
                    "keywords": ["文档"],
                    "rules": ["写文档前核对代码"],
                    "confirmedUnderstanding": ["实现优先于想象"],
                    "originalPrompt": "补充文档",
                    "correctionFeedback": "文档内容和实现不一致",
                    "finalReply": "根据真实代码更新文档",
                    "memoryPriority": 1.0,
                },
            )
            self.archive_entry(
                project_root,
                {
                    "entryType": "note",
                    "title": "缓存阈值",
                    "summary": "默认 memory threshold 是 12",
                    "scopeDecision": "project",
                    "noteReason": "长期配置约束",
                    "noteContent": ["memory threshold 默认是 12"],
                },
            )

            result = self.run_cli(
                "context",
                "--host",
                "codex",
                "--project-root",
                project_root,
                "--scope",
                "project",
                "--query",
                "先读真实实现再改文档",
                "--limit",
                "1",
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            project = output["project"]
            self.assertTrue(project["pruned"])
            self.assertEqual(project["query"], "先读真实实现再改文档")
            self.assertEqual(project["limit"], 1)
            self.assertEqual(project["totalEntries"], 3)
            self.assertEqual(project["returnedEntries"], 1)
            self.assertEqual(len(project["mistakes"]), 1)
            self.assertEqual(len(project["notes"]), 0)
            self.assertEqual(project["mistakes"][0]["title"], "先读真实实现")
            self.assertTrue(project["memoryMarkdown"])
            self.assertIn("activeEntries", project["memoryState"])

    def test_context_query_marks_only_returned_entries(self) -> None:
        with tempfile.TemporaryDirectory() as project_root:
            self.archive_entry(
                project_root,
                {
                    "entryType": "mistake",
                    "title": "先读真实实现",
                    "summary": "改文档前先核对真实实现",
                    "scopeDecision": "project",
                    "keywords": ["真实实现", "文档"],
                    "rules": ["先读真实实现再改文档"],
                    "confirmedUnderstanding": ["真实实现优先"],
                    "originalPrompt": "补文档",
                    "correctionFeedback": "你没有先读真实实现",
                    "finalReply": "已先核对实现",
                },
            )
            self.archive_entry(
                project_root,
                {
                    "entryType": "mistake",
                    "title": "数据库连接超时",
                    "summary": "连接池配置不对会导致超时",
                    "scopeDecision": "project",
                    "keywords": ["数据库", "连接池"],
                    "rules": ["数据库超时时先查连接池配置"],
                    "confirmedUnderstanding": ["连接池配置影响超时"],
                    "originalPrompt": "查数据库超时",
                    "correctionFeedback": "你忽略了连接池配置",
                    "finalReply": "已检查连接池配置",
                },
            )

            result = self.run_cli(
                "context",
                "--host",
                "codex",
                "--project-root",
                project_root,
                "--scope",
                "project",
                "--query",
                "先读真实实现再改文档",
                "--limit",
                "1",
                "--mark-retrieval",
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            project = output["project"]
            self.assertEqual(project["returnedEntries"], 1)

            catalog_path = Path(project_root) / ".mistakebook" / "state" / "catalog.json"
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            counts = {entry["title"]: entry.get("retrievalCount", 0) for entry in catalog}
            self.assertEqual(counts["先读真实实现"], 1)
            self.assertEqual(counts["数据库连接超时"], 0)


if __name__ == "__main__":
    unittest.main()
