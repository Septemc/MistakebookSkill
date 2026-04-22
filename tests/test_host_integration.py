import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS_PATH = REPO_ROOT / "hooks" / "hooks.json"
SCHOLAR_HOOK_PATH = REPO_ROOT / "hooks" / "scholar-preflight-trigger.sh"
CODEX_COMMAND_PATH = REPO_ROOT / "commands" / "scholar.md"
CODEX_SKILL_ROOT = REPO_ROOT / "codex"
CODEX_INSTALL_DOC_PATH = REPO_ROOT / ".codex" / "INSTALL.md"
README_PATH = REPO_ROOT / "README.md"
VSCODE_PROMPT_PATH = REPO_ROOT / "vscode" / "prompts" / "scholar.prompt.md"


class HostIntegrationTests(unittest.TestCase):
    def test_claude_user_prompt_submit_includes_scholar_preflight_hook(self) -> None:
        hooks_payload = json.loads(HOOKS_PATH.read_text(encoding="utf-8"))
        user_prompt_submit = hooks_payload["hooks"]["UserPromptSubmit"]
        scholar_entries = [
            entry
            for entry in user_prompt_submit
            if entry.get("matcher") == "*"
            and any(
                hook.get("type") == "command"
                and "scholar-preflight-trigger.sh" in hook.get("command", "")
                for hook in entry.get("hooks", [])
            )
        ]
        self.assertEqual(len(scholar_entries), 1)

    def test_scholar_preflight_hook_checks_config_and_emits_lightweight_instruction(self) -> None:
        script_text = SCHOLAR_HOOK_PATH.read_text(encoding="utf-8")

        self.assertIn('CONFIG="${HOME:-~}/.mistakebook/config.json"', script_text)
        self.assertIn('SCHOLAR_ENABLED=$(read_config_bool "scholar" "true")', script_text)
        self.assertIn('if [ "$SCHOLAR_ENABLED" != "true" ]; then', script_text)
        self.assertIn("[Mistakebook Scholar Preflight]", script_text)
        self.assertIn("python scripts/mistakebook_cli.py scholar --host claude", script_text)
        self.assertIn("fresh normal task", script_text)
        self.assertIn("Do not run scholar", script_text)

    def test_explicit_scholar_entrypoints_exist_for_codex_and_vscode(self) -> None:
        codex_command = CODEX_COMMAND_PATH.read_text(encoding="utf-8")
        vscode_prompt = VSCODE_PROMPT_PATH.read_text(encoding="utf-8")

        self.assertIn("python scripts/mistakebook_cli.py scholar --host codex", codex_command)
        self.assertIn("shouldInject = true", codex_command)
        self.assertIn("Ascended Mode", codex_command)

        self.assertIn("python scripts/mistakebook_cli.py scholar --host vscode", vscode_prompt)
        self.assertIn("shouldInject = true", vscode_prompt)
        self.assertIn("Ascended Mode", vscode_prompt)

    def test_codex_skill_wrappers_exist_for_chip_friendly_entrypoints(self) -> None:
        for skill_name in ("ascended", "notebook", "scholar"):
            skill_dir = CODEX_SKILL_ROOT / skill_name
            self.assertTrue((skill_dir / "SKILL.md").exists(), msg=skill_dir / "SKILL.md")
            self.assertTrue(
                (skill_dir / "agents" / "openai.yaml").exists(),
                msg=skill_dir / "agents" / "openai.yaml",
            )

    def test_codex_skill_wrappers_reference_core_protocol_sources(self) -> None:
        ascended_skill = (CODEX_SKILL_ROOT / "ascended" / "SKILL.md").read_text(encoding="utf-8")
        notebook_skill = (CODEX_SKILL_ROOT / "notebook" / "SKILL.md").read_text(encoding="utf-8")
        scholar_skill = (CODEX_SKILL_ROOT / "scholar" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("../../skills/mistakebook/SKILL.md", ascended_skill)
        self.assertIn("../../skills/mistakebook/references/ascended-mode.md", ascended_skill)

        self.assertIn("../../skills/mistakebook/SKILL.md", notebook_skill)
        self.assertIn("../../skills/mistakebook/references/archive-schema.md", notebook_skill)

        self.assertIn("../../skills/mistakebook/SKILL.md", scholar_skill)
        self.assertIn("../../commands/scholar.md", scholar_skill)

    def test_codex_docs_prefer_skill_entrypoints_over_prompt_only_examples(self) -> None:
        install_doc = CODEX_INSTALL_DOC_PATH.read_text(encoding="utf-8")
        readme = README_PATH.read_text(encoding="utf-8")

        for expected in ("$mistakebook", "$ascended", "$notebook", "$scholar"):
            self.assertIn(expected, install_doc)
            self.assertIn(expected, readme)

        self.assertIn("兼容入口", install_doc)
        self.assertIn("兼容入口", readme)

    def test_codex_docs_explain_entrypoint_roles_and_trigger_rules(self) -> None:
        install_doc = CODEX_INSTALL_DOC_PATH.read_text(encoding="utf-8")
        readme = README_PATH.read_text(encoding="utf-8")

        for doc in (install_doc, readme):
            self.assertIn("使用与触发规则", doc)
            self.assertIn("Codex 默认主入口", doc)
            self.assertIn("手动强制进入飞升模式", doc)
            self.assertIn("新任务答前预检入口", doc)
            self.assertIn("兼容入口，语义和", doc)
            self.assertIn("prompt 正文", doc)
            self.assertIn("输入框", doc)


if __name__ == "__main__":
    unittest.main()
