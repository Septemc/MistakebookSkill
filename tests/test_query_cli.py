import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "scripts" / "mistakebook_cli.py"


class MistakebookCliQueryTests(unittest.TestCase):
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

    def test_query_returns_ranked_matches(self) -> None:
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
                    "memoryPriority": 4.0,
                    "retrievalCount": 4,
                    "hitCount": 3,
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
                    "title": "缓存淘汰阈值",
                    "summary": "记住默认 memory threshold",
                    "scopeDecision": "project",
                    "noteReason": "长期配置约束",
                    "noteContent": ["memory threshold 默认是 12"],
                },
            )

            result = self.run_cli(
                "query",
                "--host",
                "codex",
                "--project-root",
                project_root,
                "--text",
                "先读真实实现再改文档",
                "--limit",
                "2",
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            self.assertEqual(output["query"], "先读真实实现再改文档")
            self.assertEqual(output["limit"], 2)
            self.assertEqual(len(output["results"]), 2)
            self.assertEqual(output["results"][0]["title"], "先读真实实现")
            self.assertGreaterEqual(output["results"][0]["score"], output["results"][1]["score"])
            self.assertTrue(output["results"][0]["matchedTerms"])

    def test_query_combines_project_and_global_scope(self) -> None:
        with tempfile.TemporaryDirectory() as project_root, tempfile.TemporaryDirectory() as global_root:
            self.archive_entry(
                project_root,
                {
                    "entryType": "mistake",
                    "title": "项目内的缓存规则",
                    "summary": "项目实现里要同步刷新缓存",
                    "scopeDecision": "project",
                    "keywords": ["缓存"],
                    "rules": ["项目内改动后刷新缓存"],
                    "confirmedUnderstanding": ["项目缓存和条目同步"],
                    "originalPrompt": "改项目缓存逻辑",
                    "correctionFeedback": "忘了刷新项目缓存",
                    "finalReply": "已刷新项目缓存",
                },
                global_root=global_root,
            )
            self.archive_entry(
                project_root,
                {
                    "entryType": "note",
                    "title": "全局记忆刷新",
                    "summary": "跨项目规则也要同步 global memory",
                    "scopeDecision": "global",
                    "keywords": ["缓存", "全局"],
                    "rules": ["全局规则变更后刷新 global memory"],
                    "confirmedUnderstanding": ["全局 memory 需要同步"],
                    "noteReason": "跨项目约束",
                    "noteContent": ["修改全局规则时刷新 global memory"],
                },
                global_root=global_root,
            )

            both_result = self.run_cli(
                "query",
                "--host",
                "codex",
                "--project-root",
                project_root,
                "--global-root",
                global_root,
                "--scope",
                "both",
                "--text",
                "刷新缓存和 global memory",
                "--limit",
                "5",
            )
            self.assertEqual(both_result.returncode, 0, msg=both_result.stderr or both_result.stdout)
            both_output = json.loads(both_result.stdout)
            scopes = {item["storeScope"] for item in both_output["results"]}
            self.assertEqual(scopes, {"project", "global"})

            project_only_result = self.run_cli(
                "query",
                "--host",
                "codex",
                "--project-root",
                project_root,
                "--global-root",
                global_root,
                "--scope",
                "project",
                "--text",
                "刷新缓存和 global memory",
                "--limit",
                "5",
            )
            self.assertEqual(project_only_result.returncode, 0, msg=project_only_result.stderr or project_only_result.stdout)
            project_only_output = json.loads(project_only_result.stdout)
            self.assertTrue(project_only_output["results"])
            self.assertEqual({item["storeScope"] for item in project_only_output["results"]}, {"project"})

    def test_query_returns_empty_results_when_nothing_matches(self) -> None:
        with tempfile.TemporaryDirectory() as project_root:
            self.archive_entry(
                project_root,
                {
                    "entryType": "mistake",
                    "title": "只和文档相关",
                    "summary": "这里记录的是文档校对经验",
                    "scopeDecision": "project",
                    "keywords": ["文档"],
                    "rules": ["写文档前核对代码"],
                    "confirmedUnderstanding": ["文档和实现要一致"],
                    "originalPrompt": "补文档",
                    "correctionFeedback": "你没核对代码",
                    "finalReply": "已按实现更新文档",
                },
            )

            result = self.run_cli(
                "query",
                "--host",
                "codex",
                "--project-root",
                project_root,
                "--text",
                "数据库连接池超时",
                "--limit",
                "3",
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            self.assertEqual(output["results"], [])


if __name__ == "__main__":
    unittest.main()
