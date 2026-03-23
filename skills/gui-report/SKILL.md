---
name: gui-report
description: "Track and report GUI agent task performance — duration, token usage, operation counts. Call at START and END of every gui-agent workflow. Also view historical task data."
---

# GUI Task Report

Track every GUI task: time, tokens, and operations.

## Automation

The tracker is **fully automatic** for most counters:

- **Auto-start**: Tracker starts on the first `detect_all` / `learn_from_screenshot` call.
  No manual `start` needed (though you can still call it explicitly).
- **Auto-tick**: All key functions in `app_memory.py` and `agent.py` auto-increment their counters.
- **Task name**: Auto-detected from `app_name/domain` on first `learn_from_screenshot` call.
- **Auto-report**: `execute_workflow()` prints a summary on completion.

## Commands

```bash
TRACKER="python3 ~/.openclaw/workspace/skills/gui-agent/skills/gui-report/scripts/tracker.py"

# Explicit start (optional — auto-starts on first detection)
$TRACKER start --task "OSWorld Task 25: United Airlines baggage calculator"

# During task — only image_calls needs manual tick:
$TRACKER tick image_calls

# Final report (saves to log, clears state)
$TRACKER report

# View history
$TRACKER history
```

## Counters

| Counter | Auto | Source |
|---------|------|--------|
| screenshots | ✅ | `learn_from_screenshot()`, `click_and_record()`, etc. |
| clicks | ✅ | `click_and_record()`, `record_page_transition()` |
| learns | ✅ | `learn_from_screenshot()` |
| transitions | ✅ | `record_page_transition()` |
| ocr_calls | ✅ | `learn_from_screenshot()`, `record_page_transition()` |
| detector_calls | ✅ | `learn_from_screenshot()` |
| image_calls | ❌ | **Manual** — LLM image tool calls |
| workflow_level0 | ✅ | `quick_template_check()` in workflow execution |
| workflow_level1 | ✅ | `identify_current_state()` in workflow execution |
| workflow_level2 | ✅ | Fallback to LLM in workflow execution |
| workflow_auto_steps | ✅ | Steps executed in auto mode |
| workflow_explore_steps | ✅ | Steps requiring LLM fallback |

## Token Tracking

Reads directly from `~/.openclaw/agents/main/sessions/sessions.json`.
`start` records baseline, `report` reads current, computes delta.

## Output Example

```
============================================================
📊 GUI Task Report: chromium/united.com
============================================================
⏱  Duration:    4.2min
🪙 Tokens:      168.4k → 195.2k (+26.8k)
   Input:       +3.2k
   Output:      +1.8k
   Cache read:  +21.8k
🔧 Operations:  5×screenshots, 4×clicks, 4×learns, 3×transitions, 2×workflow_level0, 1×workflow_level1
============================================================
```

## Inline Summary (auto_report)

During workflow execution, a one-line summary is printed automatically:

```
📊 chromium/united.com | ⏱ 2.1min | 🪙 +15.2k tokens
   🔧 3×screenshots, 2×clicks, 2×workflow_level0, 1×workflow_auto_steps
```

## Log Storage

`skills/gui-report/logs/task_history.jsonl` — one JSON per line.
`history` command shows formatted summary.
