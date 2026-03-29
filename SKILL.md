---
name: gui-agent
description: "GUI automation via visual detection. Clicking, typing, reading content, navigating menus, filling forms — all through screenshot → detect → act workflow. Supports macOS and Linux."
---

# GUI Agent

## STEP 0: Activate Platform (MANDATORY FIRST STEP)

Before any GUI operation, run:

```bash
python3 {baseDir}/scripts/activate.py
```

This detects your OS, sets up the correct action commands, and outputs platform context.
After running, `{baseDir}/actions/_actions.yaml` contains your platform's commands.

## Workflow

```
OBSERVE → LEARN → ACT → VERIFY → SAVE
```

1. **OBSERVE** — Take screenshot → run OCR + detector → understand current state
   → `read {baseDir}/skills/gui-observe/SKILL.md`

2. **LEARN** — First time with an app? Save components to memory
   → `read {baseDir}/skills/gui-learn/SKILL.md`
   → `learn_from_screenshot()` auto-outputs app tips if available

3. **ACT** — Pick target → execute using `_actions.yaml` commands → verify
   → `read {baseDir}/skills/gui-act/SKILL.md`
   → `read {baseDir}/actions/_actions.yaml` for available commands

4. **VERIFY** — Screenshot again → confirm action succeeded

5. **SAVE** — Record state transitions to memory
   → `read {baseDir}/skills/gui-memory/SKILL.md` for memory structure

## Core Rules

- **Coordinates from detection only** — OCR or GPA-GUI-Detector, NEVER from guessing
- **Look before you act** — every action must be justified by what you observed
- **image tool = understanding only** — use it to decide WHAT to click, get WHERE from OCR/detector

## Sub-Skills Reference

| Sub-Skill | When to read |
|-----------|-------------|
| `skills/gui-observe/SKILL.md` | Before screenshots or detection |
| `skills/gui-learn/SKILL.md` | Before learning a new app |
| `skills/gui-act/SKILL.md` | Before any click/type action |
| `skills/gui-memory/SKILL.md` | For memory structure details |
| `skills/gui-workflow/SKILL.md` | For multi-step navigation |
| `skills/gui-setup/SKILL.md` | For first-time machine setup |
| `skills/gui-report/SKILL.md` | For task performance reporting |
