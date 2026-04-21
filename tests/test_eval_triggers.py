import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "eval_triggers.py"


def write_fixture(
    root: Path,
    correction_matcher: str,
    ascended_matcher: str,
    should_trigger: list[str],
    should_trigger_ascended: list[str],
    should_not_trigger: list[str],
) -> None:
    hooks_dir = root / "hooks"
    eval_dir = root / "evals" / "trigger-prompts"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    eval_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "hooks": {
            "UserPromptSubmit": [
                {"matcher": correction_matcher, "hooks": []},
                {"matcher": ascended_matcher, "hooks": []},
            ]
        }
    }
    (hooks_dir / "hooks.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (eval_dir / "should-trigger.txt").write_text("\n".join(should_trigger) + "\n", encoding="utf-8")
    (eval_dir / "should-trigger-ascended.txt").write_text(
        "\n".join(should_trigger_ascended) + "\n", encoding="utf-8"
    )
    (eval_dir / "should-not-trigger.txt").write_text("\n".join(should_not_trigger) + "\n", encoding="utf-8")


class EvalTriggersScriptTests(unittest.TestCase):
    def run_script(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--root", str(root)],
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
        )

    def test_eval_triggers_passes_for_matching_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(
                root,
                correction_matcher=r"错了|重做",
                ascended_matcher=r"/ascended|最有效的方法",
                should_trigger=["你这里错了", "请重做", ""],
                should_trigger_ascended=["/ascended", "用你见过最有效的方法处理"],
                should_not_trigger=["继续实现功能", "", "解释一下代码"],
            )

            result = self.run_script(root)

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("overall: PASS", result.stdout)
            self.assertIn("should-trigger.txt", result.stdout)
            self.assertIn("should-trigger-ascended.txt", result.stdout)
            self.assertIn("should-not-trigger.txt", result.stdout)

    def test_eval_triggers_fails_for_mismatched_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_fixture(
                root,
                correction_matcher=r"错了",
                ascended_matcher=r"/ascended",
                should_trigger=["你这里错了"],
                should_trigger_ascended=["用你见过最有效的方法处理"],
                should_not_trigger=["继续实现功能"],
            )

            result = self.run_script(root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("overall: FAIL", result.stdout)
            self.assertIn("用你见过最有效的方法处理", result.stdout)
            self.assertIn("expected=ascended", result.stdout)


if __name__ == "__main__":
    unittest.main()
