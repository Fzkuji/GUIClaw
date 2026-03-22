---
name: gui-report
description: "Track and report GUI agent task performance — duration, token usage, operation counts. Call at START and END of every gui-agent workflow. Also view historical task data."
---

# GUI Task Report

Track every GUI task: time, tokens, and operations.

## When to Use

- **BEFORE** any gui-agent task: call `start`
- **AFTER** the task completes: call `report`
- **On demand**: call `history` to review past tasks

## Commands

```bash
TRACKER="python3 ~/.openclaw/workspace/skills/gui-agent/skills/gui-report/scripts/tracker.py"

# 1. Start tracking (token baseline read automatically from sessions.json)
$TRACKER start --task "OSWorld Task 25: United Airlines baggage calculator"

# 2. During task — most counters auto-tick:
#    - learn_from_screenshot() → screenshots, learns, ocr_calls, detector_calls
#    - record_page_transition() → transitions, clicks, ocr_calls
#    Only image_calls needs manual tick:
$TRACKER tick image_calls

# 3. Final report (tokens read automatically — no --context needed)
$TRACKER report

# 4. View history
$TRACKER history
```

## What's Automatic

| Counter | Auto-ticked by | Manual? |
|---------|---------------|---------|
| screenshots | `learn_from_screenshot()` | No |
| learns | `learn_from_screenshot()` | No |
| ocr_calls | `learn_from_screenshot()`, `record_page_transition()` | No |
| detector_calls | `learn_from_screenshot()` | No |
| transitions | `record_page_transition()` | No |
| clicks | `record_page_transition()` | No |
| image_calls | — | **Yes** (`$TRACKER tick image_calls`) |

## Token Tracking

Reads directly from `~/.openclaw/agents/main/sessions/sessions.json`.
No manual context size input needed — `start` records baseline, `report` reads current, computes delta.

## Output Example

```
============================================================
📊 GUI Task Report: OSWorld Task 25
============================================================
⏱  Duration:    4.2min
🪙 Tokens:      168.4k → 195.2k (+26.8k)
   Input:       +3.2k
   Output:      +1.8k
   Cache read:  +21.8k
🔧 Operations:  5×screenshots, 4×clicks, 4×learns, 3×transitions, 8×ocr_calls, 4×detector_calls, 2×image_calls
============================================================
```

## Log Storage

`skills/gui-report/logs/task_history.jsonl` — one JSON per line.
`history` command shows formatted summary.
