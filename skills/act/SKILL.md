---
name: gui-act
description: "Execute GUI actions — click components, type text, send messages. Includes pre-action verification, post-action verification, and async wait handling."
---

# Act — Execute and Verify

Detection priority: **Template Match (0.3s) → OCR (1.6s) → YOLO (0.3s) → LLM (last resort)**

## Pre-Click Verify (before every click)

1. Is the element actually on screen RIGHT NOW?
2. Is it the CORRECT element (not similar name in another window)?
3. Am I clicking inside the correct app window bounds?
4. If ANY is NO → re-observe. Do not click.

## Clicking a Known Component

```bash
python3 scripts/agent.py click --app AppName --component ButtonName
```

Manual flow:
```
1. Capture window screenshot
2. Template match against saved icon (threshold=0.8)
3. If matched (conf > 0.8):
   a. Get relative coords from match
   b. Convert: screen = window_pos + relative
   c. Verify: within window bounds?
   d. Click: cliclick c:<screen_x>,<screen_y>
4. If not matched:
   a. Run full detection (YOLO + OCR)
   b. LLM identifies target
   c. Save new component (auto-learn)
   d. Click
```

## Input Methods

```bash
# Click (logical screen coords, integers)
/opt/homebrew/bin/cliclick c:<x>,<y>

# Type ASCII only
cliclick t:"text"

# Paste CJK/special chars (MUST for Chinese)
LANG=en_US.UTF-8 pbcopy <<< "中文"
osascript -e 'tell app "System Events" to keystroke "v" using command down'

# Key press (return, esc, tab, delete, space, arrow-*, f1-f16)
cliclick kp:return

# Keyboard shortcut
osascript -e 'tell app "System Events" to keystroke "v" using command down'
```

## Sending Messages

**Pre-Send Verify** — this exists because of a real bug that sent messages to the wrong person:

1. OCR the chat HEADER (top 120px) — is the correct contact open?
2. Is the message text in the input field?
3. If NO → ABORT. Do not send.

Full message flow:
```
1. Activate app, get window bounds
2. Navigate to contact (sidebar click or search)
3. ⚠️ VERIFY: OCR chat header — correct name? If wrong → ABORT
4. Click input field → paste message (pbcopy + Cmd+V)
5. Send: cliclick kp:return
6. Verify: OCR chat area, confirm first 10 chars visible
```

## Waiting for Async UI Changes

When an action triggers a slow process (scan, download, loading):

```bash
python3 scripts/agent.py wait_for --app AppName --component ComponentName
```

- Template match polls every 10s (~0.3s/check), 120s timeout
- On success → returns coordinates, proceed
- On timeout → saves screenshot. **Do NOT blind-click** — inspect and decide
- Never use `sleep(60)` + blind click

## Post-Action Verify (after every action)

1. Screenshot again
2. Did the expected change happen?
3. Am I in the expected next state?
4. If NOT → re-observe and decide
