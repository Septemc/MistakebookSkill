import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS_PATH = REPO_ROOT / "hooks" / "hooks.json"
SCHOLAR_HOOK_PATH = REPO_ROOT / "hooks" / "scholar-preflight-trigger.sh"
CODEX_COMMAND_PATH = REPO_ROOT / "commands" / "scholar.md"
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


if __name__ == "__main__":
    unittest.main()
