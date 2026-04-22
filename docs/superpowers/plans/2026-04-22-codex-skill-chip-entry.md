# Codex Skill Chip Entry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Codex-native skill-chip entry points for `ascended`, `notebook`, and `scholar` while keeping the existing `/prompts:*` compatibility layer intact.

**Architecture:** Introduce three thin Codex skill wrapper directories under `codex/` that mirror the existing `mistakebook` Codex packaging pattern. Keep `commands/*.md` unchanged as the compatibility layer for Claude-style hosts and Codex prompts, then update the Codex installation docs and README to recommend the new skill-chip workflow first.

**Tech Stack:** Markdown skill metadata, `openai.yaml` descriptors, Python `unittest`, Codex install docs

---

### Task 1: Lock the New Codex Entry Contract with Failing Tests

**Files:**
- Modify: `tests/test_host_integration.py`
- Test: `tests/test_host_integration.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

CODEX_SKILL_ROOT = REPO_ROOT / "codex"
CODEX_INSTALL_DOC_PATH = REPO_ROOT / ".codex" / "INSTALL.md"
README_PATH = REPO_ROOT / "README.md"


def test_codex_skill_wrappers_exist_for_chip_friendly_entrypoints(self) -> None:
    for skill_name in ("ascended", "notebook", "scholar"):
        skill_dir = CODEX_SKILL_ROOT / skill_name
        self.assertTrue((skill_dir / "SKILL.md").exists(), msg=skill_dir / "SKILL.md")
        self.assertTrue((skill_dir / "agents" / "openai.yaml").exists(), msg=skill_dir / "agents" / "openai.yaml")


def test_codex_docs_prefer_skill_entrypoints_over_prompt_only_examples(self) -> None:
    install_doc = CODEX_INSTALL_DOC_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")

    for expected in ("$mistakebook", "$ascended", "$notebook", "$scholar"):
        self.assertIn(expected, install_doc)
        self.assertIn(expected, readme)

    self.assertIn("兼容入口", install_doc)
    self.assertIn("兼容入口", readme)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_host_integration.py -q`
Expected: FAIL because `codex/ascended/`, `codex/notebook/`, and `codex/scholar/` do not exist yet, and docs do not mention the new skill-first guidance.

- [ ] **Step 3: Write minimal implementation**

No production implementation in this task. Stop after the failing test is confirmed.

- [ ] **Step 4: Commit**

```bash
git add tests/test_host_integration.py
git commit -m "test: cover codex skill chip entrypoints"
```

### Task 2: Add Thin Codex Skill Wrapper Directories

**Files:**
- Create: `codex/ascended/SKILL.md`
- Create: `codex/ascended/agents/openai.yaml`
- Create: `codex/notebook/SKILL.md`
- Create: `codex/notebook/agents/openai.yaml`
- Create: `codex/scholar/SKILL.md`
- Create: `codex/scholar/agents/openai.yaml`
- Test: `tests/test_host_integration.py`

- [ ] **Step 1: Write the minimal Codex `ascended` wrapper**

```md
---
name: ascended
description: "Codex entrypoint for Mistakebook Ascended Mode. Prefer this chip-style skill over prompt expansion when you want the strongest retrieval workflow."
---

# Ascended Entry

Use `mistakebook` in Ascended Mode for the current task.

1. First output:
   `我现在会根据我见过最有效的方法来处理这个问题，我将检索我的所有知识库，我现在什么都不缺了！`
2. Then follow the existing Mistakebook Ascended Mode workflow.
3. Prefer:
   `python scripts/mistakebook_cli.py context --host codex --project-root . --scope both --mark-retrieval`
```

- [ ] **Step 2: Write the matching `openai.yaml`**

```yaml
interface:
  display_name: "飞升模式"
  short_description: "以 Codex skill chip 形式进入 mistakebook 的飞升模式"
  default_prompt: "Use $ascended to enter Mistakebook Ascended Mode for the current task."

policy:
  allow_implicit_invocation: false
```

- [ ] **Step 3: Repeat the same thin-wrapper pattern for `notebook` and `scholar`**

`notebook` should wrap Mistakebook `note` handling. `scholar` should wrap scholar preflight and say it is for fresh normal tasks, not correction or ascended flows.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_host_integration.py -q`
Expected: the wrapper existence assertions pass; the docs assertion still fails until Task 3 is complete.

- [ ] **Step 5: Commit**

```bash
git add codex/ascended codex/notebook codex/scholar tests/test_host_integration.py
git commit -m "feat: add codex skill wrapper entrypoints"
```

### Task 3: Update Codex-Facing Documentation to Recommend Skill Chips First

**Files:**
- Modify: `.codex/INSTALL.md`
- Modify: `README.md`
- Test: `tests/test_host_integration.py`

- [ ] **Step 1: Update the Codex install doc**

Document:

1. Skill-first installation for `mistakebook`, `ascended`, `notebook`, `scholar`
2. Prompt files remain optional compatibility entrypoints
3. Validation examples should show `$mistakebook`, `$ascended`, `$notebook`, `$scholar` first

- [ ] **Step 2: Update the README Codex usage section**

Document:

1. Codex preferred entrypoints are the four `$...` skill chips
2. `/prompts:*` remains the compatibility layer
3. Clarify the UX reason: skill entrypoints avoid prompt-body expansion in the composer

- [ ] **Step 3: Run test to verify it passes**

Run: `python -m pytest tests/test_host_integration.py -q`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add .codex/INSTALL.md README.md tests/test_host_integration.py
git commit -m "docs: recommend codex skill chip entrypoints"
```

### Task 4: Run Focused Regression Tests

**Files:**
- Test: `tests/test_host_integration.py`
- Test: `tests/test_eval_triggers.py`
- Test: `tests/test_mistakebook_cli.py`

- [ ] **Step 1: Run the focused test set**

Run: `python -m pytest tests/test_host_integration.py tests/test_eval_triggers.py tests/test_mistakebook_cli.py -q`
Expected: PASS

- [ ] **Step 2: If the focused suite passes, stop**

Do not broaden into unrelated refactors in this task.

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "test: verify codex skill chip entry integration"
```

## Spec Coverage Check

The spec requires:

1. New Codex skill wrapper directories
2. Codex docs to prefer skill-chip entrypoints
3. Existing `commands/*.md` compatibility preserved
4. Regression coverage

Tasks 1-4 cover all four requirements. No open gaps remain.
