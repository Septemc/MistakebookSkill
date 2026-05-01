<div align="center">

[中文](./README.md) · **English**

# 📝 MistakeBook Skill

#### I have done tens of thousands of practice problems, and I have summarized a vast amount of wrong answers. Now, I am invincible!
Correction Loop + Ascended Mode + Cache-based Memory

[![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)](./LICENSE)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-8B5CF6?style=for-the-badge)](https://agentskills.io)

![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-D97706?style=flat-square&logo=anthropic&logoColor=white)
![Codex](https://img.shields.io/badge/Codex-Skill-10B981?style=flat-square&logo=openai&logoColor=white)

</div>

# Mistakebook Skill

> I have done tens of thousands of practice problems, and I have summarized a vast amount of wrong answers. Now, I am invincible!

![](docs/assets/825b6024898386ec7ccef3496b3efe26.jpg)

---

## 📦 Installation

In Claude Code, Codex, or other Skill-supporting Agents, simply say:

```
Install Mistakebook Skill: https://github.com/Septemc/MistakebookSkill.git
```

---


## What Problem Does This Project Solve?

When an AI Agent is corrected by a user, common problems are not "insufficient apology", but rather:

1. Fixed this round, same error next round
2. User corrections only exist in chat history, not structured experience
3. Corrected multiple times, but Agent still patches superficially
4. No distinction between "project-specific experience" and "cross-project general rules"
5. Items worth long-term attention but not necessarily mistakes are not preserved
6. Memory grows indefinitely, no one dares to read it, no one knows what to forget

`Mistakebook Skill` aims to transform these problems into real memory assets.

## Core Capabilities

### 1. Unified Loop: Mistakes + Notebook

This project no longer only handles mistakes, but unifies two scenarios:

1. User is correcting you
   - Enter `mistake` loop
2. User asks you to preserve long-term items
   - Enter `note` loop

### 2. Fixed Correction Loop

Once entering correction mode, Agent must first output the fixed activation text:

`<Mistakebook.Skill>I will now correct my mistake based on your feedback, continue correcting until completion, and archive it to my mistakebook.`

After each correction turn, if the user hasn't explicitly confirmed completion, must end with the fixed follow-up:

`Have I fully understood the issue and successfully corrected the mistake? If not, please teach me again. (If I have completed the correction, please let me know so I can archive it to my mistakebook.)`

### 3. Fixed Notebook Follow-up

Whenever a stable long-term takeaway worth preserving is formed in the reply, Agent should append:

`If this item is worth long-term attention, you can also tell me "write to notebook" and I will archive it to the notebook and refresh my memory.`

### 4. Only Archive After Explicit Confirmation

Only when the user explicitly confirms is archiving allowed:

1. For `mistake`
   - `That's correct now`
   - `Archive it`
   - `Write to mistakebook`
   - `Correction complete`
2. For `note`
   - `Write to notebook`
   - `Note this down`
   - `Preserve this long-term`

### 5. Memory is a Cache, Not a Full Repository

After each `mistake` or `note` entry, both are refreshed:

1. Project memory
2. Global memory

These memory files are positioned as cache layers:

1. Only retain high-density, executable content worth re-injecting in the future
2. After reaching threshold, stop mechanical accumulation
3. Low-hit, long-inactive content temporarily exits cache
4. Detailed entries always remain in detailed archive directories

### 6. Ascended Mode

When ordinary corrections are insufficient, or the user explicitly requests:

1. `Use the most effective method you have seen to handle this`
2. `/ascended`

Agent will upgrade to Ascended Mode.

When entering Ascended Mode, Agent must first output:

`I will now handle this problem using the most effective method I have seen. I will search all my knowledge bases. I am ready!`

Ascended Mode will thoroughly retrieve:

1. Project-level mistake archive
2. Project-level notebook
3. Project-level memory
4. Project-level cache state
5. Global-level mistake archive
6. Global-level notebook
7. Global-level memory
8. Global-level cache state
9. Real files, real outputs, real docs in current repo relevant to the problem
10. Complete correction chain / item chain of current case

### 7. Scholar Mode

When this is a new normal task, not correction, notebook archiving, or Ascended Mode:

1. First run `scholar`
2. Only give a one-line history reminder when high-confidence match found

Agent enters Scholar Mode preflight.

When entering Scholar Mode, Agent should preferentially execute:

`python scripts/mistakebook_cli.py scholar --host codex --project-root . --scope both --text "<current task>"`

Scholar Mode performs these tasks as lightly as possible:

1. Retrieve project-level mistake archive
2. Retrieve project-level notebook
3. Retrieve project-level memory
4. Retrieve global-level mistake archive
5. Retrieve global-level notebook
6. Retrieve global-level memory
7. Sort candidate cases by field match and memory score
8. Return only most relevant high-confidence results
9. Only output one `message` line when `shouldInject = true`
10. Don't write archives, don't refresh memory, don't increase retrieval accounting

Boundary between Scholar Mode and Ascended Mode:

1. Scholar Mode is responsible for pre-answer mistake prevention
2. Ascended Mode is responsible for post-failure escalation
3. Once entering correction loop, notebook archiving, or Ascended Mode, Scholar Mode must stop

## Repository Structure

```text
.
├─ .claude-plugin/              # Claude-style plugin metadata
├─ .codex/                      # Codex installation docs
├─ codex/ascended/              # Codex Ascended Mode skill-chip wrapper
├─ codex/mistakebook/           # Codex main skill-chip entry
├─ codex/notebook/              # Codex Notebook skill-chip wrapper
├─ codex/scholar/               # Codex Scholar skill-chip wrapper
├─ commands/                    # Manual command entries
├─ evals/                       # Trigger word regression samples
├─ hooks/                       # Claude-style auto-trigger / restore hooks
├─ scripts/                     # Archive, cache consolidation & context export CLI
├─ skills/mistakebook/          # Universal core Skill
├─ vscode/                      # VSCode Copilot adaptation
├─ plugin.json                  # Top-level plugin package metadata
└─ README.md
```

## Key Files

- [skills/mistakebook/SKILL.md](./skills/mistakebook/SKILL.md)
  - Universal core protocol
- [skills/mistakebook/references/activation-patterns.md](./skills/mistakebook/references/activation-patterns.md)
  - Mistake / Notebook / Ascended Mode trigger rules
- [skills/mistakebook/references/storage-and-scope.md](./skills/mistakebook/references/storage-and-scope.md)
  - `failures/`, `notes/`, `memory/`, `state/` layout and cache strategy
- [skills/mistakebook/references/archive-schema.md](./skills/mistakebook/references/archive-schema.md)
  - `mistake` / `note` unified schema
- [skills/mistakebook/references/ascended-mode.md](./skills/mistakebook/references/ascended-mode.md)
  - Ascended Mode protocol
- [scripts/mistakebook_cli.py](./scripts/mistakebook_cli.py)
  - Bootstrap, archive, touch, consolidate, context, query, scholar CLI

## Storage Structure

All Agent tools (Codex, Claude Code, VSCode, generic) share unified storage paths:

- **Project-level**: `<project>/.mistakebook/`
- **Global-level**: `~/.mistakebook/`

Each store contains at minimum:

```text
.mistakebook/
├─ failures/
│  ├─ INDEX.md
│  └─ <timestamp>_<slug>.md
├─ notes/
│  ├─ INDEX.md
│  └─ <timestamp>_<slug>.md
├─ memory/
│  ├─ PROJECT_MEMORY.md
│  └─ GLOBAL_MEMORY.md
└─ state/
   ├─ catalog.json
   └─ memory_state.json
```

### Migrating from Legacy Paths

If you previously used legacy storage paths (`.codex/mistakebook/`, `.claude/mistakebook/`, `.vscode/mistakebook/`), run this command to automatically migrate to unified paths:

```bash
python scripts/mistakebook_cli.py migrate --host codex --project-root .
```

## CLI Usage

Local script entry: [scripts/mistakebook_cli.py](./scripts/mistakebook_cli.py).

### 1. Bootstrap

```bash
python scripts/mistakebook_cli.py bootstrap --host codex --project-root .
```

### 2. Archive Entry

```bash
python scripts/mistakebook_cli.py archive --host codex --project-root . --payload-file payload.json
python scripts/mistakebook_cli.py archive --host codex --project-root . --payload '{"entryType":"note","title":"...","summary":"..."}'
python scripts/mistakebook_cli.py archive --host codex --project-root . --payload-stdin
```

### 3. Query

```bash
python scripts/mistakebook_cli.py query --host codex --project-root . --scope both --text "read real implementation first" --limit 3
```

### 4. Touch (Record Hit/Retrieval)

```bash
python scripts/mistakebook_cli.py touch --host codex --project-root . --scope both --case-id <case-id> --kind hit
```

### 5. Consolidate

```bash
python scripts/mistakebook_cli.py consolidate --host codex --project-root . --scope both
```

### 6. Context Export

```bash
python scripts/mistakebook_cli.py context --host codex --project-root . --scope both --mark-retrieval
```

### 7. Status

```bash
python scripts/mistakebook_cli.py status --host codex --project-root . --scope both
```

### 8. Migrate

```bash
python scripts/mistakebook_cli.py migrate --host codex --project-root .
```

### 9. Config

```bash
python scripts/mistakebook_cli.py config --auto-detect on
python scripts/mistakebook_cli.py config --auto-detect off
```

## Recommended Workflows

### Scenario 1: Auto-Enter Correction Mode

1. User points out error
2. Skill auto-triggers
3. Agent outputs fixed activation text
4. Agent corrects based on feedback
5. Fixed follow-up at end of each turn
6. If long-term item formed, ask about notebook
7. User explicitly confirms completion
8. Agent archives `mistake` and refreshes memory

### Scenario 2: Actively Record Items

1. User says "write to notebook"
2. Agent organizes current item
3. Agent explains why it's worth preserving
4. Agent asks about writing to notebook
5. User explicitly confirms
6. Agent archives `note` and refreshes memory

### Scenario 3: Auto-Escalate to Ascended Mode

1. User has corrected Agent twice or more
2. User still explicitly says "still wrong / not fixed"
3. Agent auto-enters Ascended Mode
4. Agent outputs fixed Ascended Mode reply
5. Agent comprehensively retrieves mistakes, notes, memory, and knowledge base
6. Explains why previous corrections failed
7. Chooses most effective method to re-handle

### Scenario 4: Manually Start Ascended Mode

1. User inputs `/ascended`
2. Or user says: `Use the most effective method you have seen to handle this`
3. Agent outputs Ascended Mode fixed reply
4. Agent retrieves project/global mistakes, notes, memory, and real files
5. Agent explains why previous attempts failed
6. Agent chooses most effective method to re-handle

## License

MIT License - see [LICENSE](./LICENSE)
