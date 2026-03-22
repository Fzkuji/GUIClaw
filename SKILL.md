---
name: gui-agent
description: "ALL interactions with ANY app — whether built-in (Finder, Safari, System Settings) or third-party (WeChat, Chrome, Slack) — MUST go through this skill. Clicking, typing, reading content, sending messages, navigating menus, filling forms: everything uses visual detection (screenshot → template match → click). This is the ONLY way to operate apps. Never bypass with CLI commands, AppleScript, or Accessibility APIs."
---

# GUI Agent Skill

You ARE the agent loop. Every GUI task follows this flow:

```
OBSERVE → ENSURE APP READY → ACT → VERIFY (auto) → RECORD TRANSITION → REPORT
```

## Sub-Skills (MANDATORY — read ALL before first GUI action)

**Before doing ANY GUI operation, you MUST `read` these files. No exceptions. They are short (~100 lines each).**

```
read skills/gui-observe/SKILL.md   # How to screenshot and detect state
read skills/gui-learn/SKILL.md     # How to learn new app UIs
read skills/gui-act/SKILL.md       # How to click, type, send messages
read skills/gui-memory/SKILL.md    # How to save/load components and states
```

**Read these when needed:**

```
read skills/gui-workflow/SKILL.md  # State graph navigation (multi-step tasks)
read skills/gui-setup/SKILL.md    # First-time setup on new machine
read skills/gui-report/SKILL.md   # Performance tracking
```

| Step | Skill | Mandatory? |
|------|-------|-----------|
| **Observe** | `skills/gui-observe/SKILL.md` | ✅ Always read first |
| **Learn** | `skills/gui-learn/SKILL.md` | ✅ Always read first |
| **Act** | `skills/gui-act/SKILL.md` | ✅ Always read first |
| **Memory** | `skills/gui-memory/SKILL.md` | ✅ Always read first |
| **Workflow** | `skills/gui-workflow/SKILL.md` | When doing multi-step navigation |
| **Setup** | `skills/gui-setup/SKILL.md` | First-time setup only |
| **Report** | `skills/gui-report/SKILL.md` | When tracking performance |

## Core Commands

**exec timeout**: Always use `timeout=60` for GUI commands. Commands return immediately when done; the timeout only caps maximum wait.

```bash
source ~/gui-actor-env/bin/activate
cd ~/.openclaw/workspace/skills/gui-agent

# Observe
python3 scripts/agent.py learn --app AppName        # Detect + save components
python3 scripts/agent.py detect --app AppName        # Match known components
python3 scripts/agent.py list --app AppName          # List saved components

# Act
python3 scripts/agent.py click --app AppName --component ButtonName
python3 scripts/agent.py open --app AppName
python3 scripts/agent.py cleanup --app AppName

# State graph
python3 scripts/app_memory.py transitions --app AppName     # View state graph
python3 scripts/app_memory.py path --app AppName --component from_state --contact to_state  # Find route

# Messaging (prints guidance, agent executes step by step)
python3 scripts/agent.py send_message --app WeChat --contact "小明" --message "明天见"
```

## Execution Flow

### STEP 0: OBSERVE
Take screenshot. Use `image` tool to **understand** current state (what app, what page, what's visible). First time only — subsequent steps use component detection.

### STEP 1: ENSURE APP READY
If app not in memory → `learn`. If component not found → `learn` current state.
Component not matching ≠ lower threshold. It means the component isn't on screen — re-learn to discover what IS on screen.

### STEP 2: ACT
`click_component` handles everything automatically:
1. Screenshot (one, shared for detection + matching)
2. Detect visible components (template match, no LLM)
3. Match target component → get precise coordinates
4. Click
5. Detect visible components again
6. Record state transition (from → click → to)
7. Report: appeared/disappeared components, current state

### STEP 3: VERIFY (automatic)
- **Known state**: verifies expected components appeared (no screenshot needed)
- **Mismatch**: agent should then screenshot + `image` tool to diagnose

### STEP 4: STATE TRANSITION (pending)
Every click records a **pending** transition. Pending = NOT saved yet.
- **Workflow succeeds** → `confirm_transitions(app)` → saved permanently
- **Workflow fails/aborts** → `discard_transitions(app)` → thrown away
- This prevents trial-and-error clicks from polluting the state graph

### STEP 5: COMMIT OR DISCARD
After the full workflow completes:
- **Success** → `confirm_transitions(app)` + `save_workflow(app, name, target_state)`
- **Failure** → `discard_transitions(app)` — graph stays clean

### STEP 6: REPORT

Use `gui-report` skill's tracker:

1. **Task start**: `session_status` → note context size → `tracker.py start --task "..." --context X`
2. **During task**: clicks/screenshots/learns auto-tick via `app_memory.py`. Only `image_calls` needs manual tick.
3. **Task end**: `session_status` → `tracker.py report --context X`

Outputs duration, context delta, and operation counts. Use `tracker.py history` to review past tasks.

---

## ⛔ ABSOLUTE RULES (read every time, no exceptions)

**WHERE DO CLICK COORDINATES COME FROM?**

```
✅ ALLOWED coordinate sources:
   1. GPA-GUI-Detector (detect_icons) → bounding box center
   2. Apple Vision OCR (detect_text) → text bounding box center
   3. Template matching → saved component position

❌ FORBIDDEN:
   - LLM/vision model guessing coordinates ("it looks like it's around 500, 300")
   - Hardcoded pixel positions from memory or documentation
   - Coordinates from image tool analysis (image tool = understanding ONLY)
```

**Every click**: screenshot → run GPA-GUI-Detector and/or OCR → get coordinates from detection result → click that coordinate. No exceptions. If detection can't find the element, re-detect or re-learn — do NOT guess.

**This applies everywhere**: local Mac apps, remote VMs (OSWorld), any platform. For remote VMs: download screenshot to Mac → run detection locally → send click coordinates back to VM.

## Key Principles

1. **Vision-driven, no shortcuts** — screenshot → detect → match → click. Only allowed system calls: `activate` (bring to front), `screencapture`, `platform_input.py` (pynput click/type).
2. **Coordinates from detection only** — see ABSOLUTE RULES above. The `image` tool is for understanding ("what is this?", "which button should I click?"), NEVER for getting pixel coordinates.
3. **Not found = not on screen** — don't lower thresholds. Re-learn current state to discover what IS on screen.
4. **State graph drives navigation** — each click records a transition. Use `find_path()` to route between states.
5. **First time: screenshot + image. Repeat: detection only** — saves tokens on known workflows.
6. **Paste > Type** for CJK text
7. **Integer logical coordinates** — pynput uses screen logical pixels
8. **ALWAYS save to memory** — every GUI operation MUST save detection results, learned components, and state information to `memory/apps/<appname>/`. This is the core of the system. Even for one-off tasks or benchmarks (e.g., OSWorld), save what you learn about each app. Memory is local (gitignored) but essential — it's what makes GUIClaw learn and improve.

## Safety Rules

1. **Full-screen search + window validation** — match on full screen, reject matches outside target app's window bounds
2. **App switch detection** — `click_component` checks frontmost app after every click
3. **No wrong-app learning** — validate frontmost app before learn
4. **Reject tiny templates** — <30×30 pixels produce false matches
5. **Never send screenshots to chat** — internal detection only
6. **NEVER quit the communication app** — if a dialog asks to quit apps (like CleanMyMac's "Quit All"), NEVER quit Discord/Telegram/WhatsApp or whatever channel you're communicating through. Instead: click "Ignore" to skip. Quitting the comms app disconnects you from the user.
7. **Watch for new dialogs/windows** — clicking a button may spawn a new dialog or window. After clicking, check if a new window appeared and handle it before continuing.
8. **Every click uses `click_and_record` or `click_component`** — never raw `click_at()`. Every click must record a state transition.

## Input Methods (platform_input.py)

```python
from platform_input import click_at, paste_text, key_press, key_combo, screenshot, 
    activate_app, get_clipboard, set_clipboard, mouse_right_click
```

No cliclick. No osascript for input. pynput only.

## File Structure

```
gui-agent/
├── SKILL.md              # This file
├── skills/               # Sub-skills (read on demand)
├── scripts/
│   ├── agent.py          # CLI entry point
│   ├── app_memory.py     # Components, states, transitions, matching
│   ├── platform_input.py # Cross-platform input (pynput)
│   ├── ui_detector.py    # GPA-GUI-Detector + OCR detection
│   └── template_match.py # Legacy template matching
├── memory/               # Visual memory (gitignored)
│   ├── apps/<appname>/profile.json  # Components + states + transitions
│   └── meta_workflows/
└── README.md
```
