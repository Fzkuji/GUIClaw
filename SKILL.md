---
name: gui-agent
description: "Visually operate any application on macOS — native apps, browsers, or anything with a GUI window. Open apps, click buttons, type text, send messages, fill forms, navigate menus, all driven by visual UI detection. Use when the task requires interacting with what's on screen."
---

# GUI Agent Skill

You ARE the agent loop. Every GUI task follows this flow, in order:

```
INTENT MATCH → OBSERVE → ENSURE APP READY → ACT → VERIFY → SAVE WORKFLOW → REPORT
```

## Sub-Skills

Each step has detailed instructions in its own skill file:

| Step | Skill | When to read |
|------|-------|-------------|
| **Observe** | `skills/observe/SKILL.md` | Before any action — screenshot, OCR, identify state |
| **Learn** | `skills/learn/SKILL.md` | App not in memory, or match rate < 80% |
| **Act** | `skills/act/SKILL.md` | Clicking, typing, sending messages, waiting for UI |
| **Workflow** | `skills/workflow/SKILL.md` | Intent matching, saving/replaying workflows, meta-workflows |
| **Browser** | `skills/browser/SKILL.md` | Operating browsers — two-layer memory, navigation, per-site learning |
| **Setup** | `skills/setup/SKILL.md` | First-time setup on a new machine |

Read the relevant sub-skill when you reach that step. You don't need to read all of them upfront.

## agent.py — Unified Entry Point

**All GUI operations go through `scripts/agent.py`.** Do not call `app_memory.py` or `gui_agent.py` directly.

```bash
source ~/gui-agent-env/bin/activate

# Core operations
python3 scripts/agent.py open --app AppName
python3 scripts/agent.py learn --app AppName
python3 scripts/agent.py detect --app AppName
python3 scripts/agent.py click --app AppName --component ButtonName
python3 scripts/agent.py list --app AppName
python3 scripts/agent.py read_screen --app AppName
python3 scripts/agent.py wait_for --app AppName --component X
python3 scripts/agent.py cleanup --app AppName
python3 scripts/agent.py navigate --url "https://example.com"
python3 scripts/agent.py workflows --app AppName
python3 scripts/agent.py all_workflows

# Messaging
python3 scripts/agent.py send_message --app WeChat --contact "小明" --message "明天见"
python3 scripts/agent.py read_messages --app WeChat --contact "小明"
```

agent.py automatically handles:
- New app → learn → plan
- Known app → eval (template match; ≥80% proceed, <80% re-learn)
- Error → re-learn + new plan
- Chinese aliases: 微信→WeChat, 浏览器→Chrome

## Execution Flow

### STEP -1: INTENT MATCHING
→ Details: `skills/workflow/SKILL.md`

Match user request to saved workflows before doing anything. If matched, use workflow steps as plan. If not, proceed and save after success.

### STEP 0: OBSERVE
→ Details: `skills/observe/SKILL.md`

Screenshot, identify current state. Record `session_status` for token reporting.

### STEP 1: ENSURE APP READY
→ Details: `skills/learn/SKILL.md`

Check if app is in memory. If not → learn. If match rate < 80% → re-learn. This is YOUR responsibility — do not wait for the user.

### STEP 2: LEARN (when needed)
→ Details: `skills/learn/SKILL.md`

Detect all components (YOLO + OCR), identify them, filter, save to memory. Privacy check: delete personal info.

### STEP 3: ACT
→ Details: `skills/act/SKILL.md`

Execute clicks, typing, sending. Pre-verify before every click. Pre-verify contact before every message send.

### STEP 4: POST-ACTION VERIFY
→ Details: `skills/act/SKILL.md`

Screenshot after every action. Did the expected change happen? If not → re-observe.

### STEP 5: SAVE WORKFLOW
→ Details: `skills/workflow/SKILL.md`

Save successful multi-step sequences for future replay.

### STEP 6: REPORT

Every GUI task ends with a report:
```
⏱ 45.2s | 📊 +10k tokens (85k→95k) | 🔧 3 screenshots, 2 clicks, 1 learn
```
Compare `session_status` from STEP 0 vs now.

---

## Key Principles

1. **Vision-driven, no shortcuts** — every GUI interaction goes through the visual pipeline (screenshot → detect → match → click). Do not use system commands (`open <url>`, `osascript tell app to set URL`, CLI tools) to manipulate app state. Only allowed system calls: `activate` (bring window to front), `screencapture` (take screenshot), `cliclick` (click/type after visual detection provides coordinates).
2. **Memory first, detect second** — template match before YOLO+OCR
3. **Template > OCR > YOLO > LLM** — cheapest method first
4. **Relative coordinates** — all positions relative to window top-left
5. **Window-based, not screen-based** — capture and operate within target window only
6. **Paste > Type** for CJK text and special chars
7. **Learn incrementally** — save new components after each interaction
8. **Integer coordinates only** — cliclick requires integers
9. **Learn once, match forever** — UI positions are stable unless app updates

## Safety Rules

These exist because of real bugs:

1. **Verify before sending** — always OCR the chat header to confirm correct contact
2. **Stay within window bounds** — get bounds first, filter all OCR/clicks
3. **No wrong-app learning** — validate window bounds before auto_learn
4. **Reject tiny templates** — <30×30 pixels produce false matches
5. **LLM never provides coordinates** — detection tools provide coordinates, you decide what to click by name
6. **Never send screenshots to conversation** — internal detection only

## Memory System

```
memory/apps/<appname>/
├── profile.json        # Component registry + page/region/overlay structure
├── summary.json        # App overview
├── components/         # Cropped component images (PNG)
├── pages/              # Annotated screenshots
└── workflows/          # Saved workflow sequences

memory/meta_workflows/  # Cross-app orchestration
```

### Profile Structure

```json
{
  "app": "AppName",
  "window_size": [w, h],
  "pages": {
    "main": {
      "fingerprint": { "expect_text": ["Chat", "Cowork"] },
      "regions": {
        "sidebar": { "position": "left", "stable": true, "components": ["Search"] }
      },
      "transitions": { "Cmd+,": { "to": "settings" } }
    }
  },
  "overlays": {
    "menu": { "trigger": "profile_area", "dismiss": ["Esc"] }
  },
  "components": {
    "Search": { "type": "icon", "rel_x": 116, "rel_y": 144, "page": "main" }
  }
}
```

### Key Concepts

| Concept | Description |
|---------|------------|
| **Page** | Full UI state, mutually exclusive (main, settings) |
| **Region** | Area within a page (sidebar, toolbar, content) |
| **Overlay** | Temporary popup over a page (menu, dialog) |
| **Fingerprint** | Text to identify current page |
| **Transition** | State change on click/key |

## File Structure

```
gui-agent/
├── SKILL.md              # This file (main orchestrator)
├── skills/               # Sub-skills (read on demand)
│   ├── observe/SKILL.md
│   ├── learn/SKILL.md
│   ├── act/SKILL.md
│   ├── workflow/SKILL.md
│   ├── browser/SKILL.md
│   └── setup/SKILL.md
├── scripts/              # Core scripts
│   ├── agent.py, ui_detector.py, app_memory.py, gui_agent.py, template_match.py
├── memory/               # Visual memory (gitignored)
│   ├── apps/<appname>/
│   └── meta_workflows/
├── actions/              # Atomic operations
├── docs/
└── README.md
```
