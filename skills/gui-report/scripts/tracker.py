#!/usr/bin/env python3
"""GUI task tracker — automatic token tracking via OpenClaw sessions.json.

No manual context passing needed. Reads token usage directly from
~/.openclaw/agents/main/sessions/sessions.json.

Usage:
    tracker.py start --task "Task name" [--session SESSION_KEY]
    tracker.py tick screenshots|clicks|learns|transitions|image_calls [-n N]
    tracker.py note "some text"
    tracker.py report [--session SESSION_KEY]
    tracker.py history [--limit N]
"""

import argparse
import json
import os
import time
from pathlib import Path

STATE_FILE = Path(__file__).parent / ".tracker_state.json"
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "task_history.jsonl"

# OpenClaw sessions file
SESSIONS_FILE = Path.home() / ".openclaw" / "agents" / "main" / "sessions" / "sessions.json"

# Default session key (Discord DM — most common for GUI tasks)
DEFAULT_SESSION_KEYS = [
    # Try to find the active session automatically
]


def _find_session_key(preferred=None):
    """Find the active session key from sessions.json."""
    if preferred:
        return preferred

    if not SESSIONS_FILE.exists():
        return None

    with open(SESSIONS_FILE) as f:
        sessions = json.load(f)

    # Heuristic: find the most recently updated discord:direct session
    best_key = None
    best_time = 0
    for key, data in sessions.items():
        if "discord:direct" in key or "main:main" in key:
            updated = data.get("updatedAt", 0)
            if updated > best_time:
                best_time = updated
                best_key = key

    return best_key


def _read_tokens(session_key=None):
    """Read current token usage from OpenClaw sessions.json."""
    if not SESSIONS_FILE.exists():
        return None

    try:
        with open(SESSIONS_FILE) as f:
            sessions = json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

    key = session_key or _find_session_key()
    if not key or key not in sessions:
        return None

    s = sessions[key]
    return {
        "totalTokens": s.get("totalTokens", 0),
        "inputTokens": s.get("inputTokens", 0),
        "outputTokens": s.get("outputTokens", 0),
        "cacheRead": s.get("cacheRead", 0),
        "cacheWrite": s.get("cacheWrite", 0),
        "contextTokens": s.get("contextTokens", 0),
        "sessionKey": key,
    }


# All known counters (for start() initialization and reporting)
COUNTERS = [
    "screenshots", "clicks", "learns", "transitions",
    "image_calls", "ocr_calls", "detector_calls",
    # Workflow verification counters
    "workflow_level0",        # quick_template_check verifications
    "workflow_level1",        # detect_all full verifications
    "workflow_level2",        # fallback to LLM
    "workflow_auto_steps",    # steps executed in auto mode
    "workflow_explore_steps", # steps executed in explore mode
]


def start(args):
    """Record baseline before a GUI task."""
    session = args.session if hasattr(args, 'session') else None
    task = args.task if hasattr(args, 'task') else None
    tokens = _read_tokens(session)

    state = {
        "task": task or "unnamed",
        "start_time": time.time(),
        "session_key": tokens["sessionKey"] if tokens else None,
        "tokens_start": tokens,
        "notes": [],
    }
    # Initialize all counters to 0
    for c in COUNTERS:
        state[c] = 0

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

    if tokens:
        print(f"📊 Tracker started: {state['task']}")
        print(f"   Session: {tokens['sessionKey']}")
        print(f"   Baseline: {_fmt(tokens['totalTokens'])} total tokens")
    else:
        print(f"📊 Tracker started: {state['task']} (⚠ could not read session tokens)")


def tick(args):
    """Increment a counter."""
    if not STATE_FILE.exists():
        return  # Silent — don't break callers
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
        key = args.counter if hasattr(args, 'counter') else args
        n = args.n if hasattr(args, 'n') and args.n else 1
        state[key] = state.get(key, 0) + n
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception:
        pass  # Never fail — tracking is best-effort


def tick_counter(counter, n=1):
    """Programmatic tick — called by app_memory.py functions."""
    if not STATE_FILE.exists():
        return
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
        state[counter] = state.get(counter, 0) + n
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception:
        pass


def update_task_name(name):
    """Update the task name in running tracker state.

    Called by learn_from_screenshot with app_name + domain.
    Only updates if current name is 'auto' (don't overwrite explicit names).
    """
    if not STATE_FILE.exists():
        return
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
        # Only update if auto-started (don't overwrite explicit task names)
        if state.get("task") in ("auto", "unnamed"):
            state["task"] = name
            with open(STATE_FILE, "w") as f:
                json.dump(state, f)
    except Exception:
        pass


def auto_report():
    """Generate report and return formatted string (don't print).

    Differences from report():
    - Returns string instead of printing
    - Does NOT delete state file (tracker continues running)
    - Does NOT save to log (wait for formal report() to save)
    """
    if not STATE_FILE.exists():
        return "⚠ No active tracker."

    try:
        with open(STATE_FILE) as f:
            state = json.load(f)

        elapsed = time.time() - state["start_time"]
        tokens_now = _read_tokens(state.get("session_key"))
        tokens_start = state.get("tokens_start", {})

        total_start = tokens_start.get("totalTokens", 0) if tokens_start else 0
        total_end = tokens_now.get("totalTokens", 0) if tokens_now else 0
        token_delta = total_end - total_start

        input_start = tokens_start.get("inputTokens", 0) if tokens_start else 0
        input_end = tokens_now.get("inputTokens", 0) if tokens_now else 0
        output_start = tokens_start.get("outputTokens", 0) if tokens_start else 0
        output_end = tokens_now.get("outputTokens", 0) if tokens_now else 0
        cache_start = tokens_start.get("cacheRead", 0) if tokens_start else 0
        cache_end = tokens_now.get("cacheRead", 0) if tokens_now else 0

        # Format time
        if elapsed < 60:
            time_str = f"{elapsed:.1f}s"
        elif elapsed < 3600:
            time_str = f"{elapsed/60:.1f}min"
        else:
            time_str = f"{elapsed/3600:.1f}h"

        # Operations
        ops = []
        for key in COUNTERS:
            v = state.get(key, 0)
            if v > 0:
                ops.append(f"{v}×{key}")

        lines = []
        lines.append(f"📊 {state['task']} | ⏱ {time_str} | 🪙 +{_fmt(token_delta)} tokens")
        if ops:
            lines.append(f"   🔧 {', '.join(ops)}")
        return "\n".join(lines)

    except Exception as e:
        return f"⚠ auto_report failed: {e}"


def note(args):
    """Add a note."""
    if not STATE_FILE.exists():
        return
    with open(STATE_FILE) as f:
        state = json.load(f)
    text = args.text if hasattr(args, 'text') else args
    state.setdefault("notes", []).append(text)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print(f"  📝 Note added")


def report(args):
    """Generate final report with automatic token delta."""
    if not STATE_FILE.exists():
        print("⚠ No active tracker.")
        return

    with open(STATE_FILE) as f:
        state = json.load(f)

    elapsed = time.time() - state["start_time"]
    tokens_now = _read_tokens(state.get("session_key") or (args.session if hasattr(args, 'session') else None))
    tokens_start = state.get("tokens_start", {})

    # Token deltas
    total_start = tokens_start.get("totalTokens", 0) if tokens_start else 0
    total_end = tokens_now.get("totalTokens", 0) if tokens_now else 0
    token_delta = total_end - total_start

    cache_read_start = tokens_start.get("cacheRead", 0) if tokens_start else 0
    cache_read_end = tokens_now.get("cacheRead", 0) if tokens_now else 0
    cache_delta = cache_read_end - cache_read_start

    input_start = tokens_start.get("inputTokens", 0) if tokens_start else 0
    input_end = tokens_now.get("inputTokens", 0) if tokens_now else 0
    output_start = tokens_start.get("outputTokens", 0) if tokens_start else 0
    output_end = tokens_now.get("outputTokens", 0) if tokens_now else 0

    # Format time
    if elapsed < 60:
        time_str = f"{elapsed:.1f}s"
    elif elapsed < 3600:
        time_str = f"{elapsed/60:.1f}min"
    else:
        time_str = f"{elapsed/3600:.1f}h"

    # Operations
    ops = []
    for key in COUNTERS:
        v = state.get(key, 0)
        if v > 0:
            ops.append(f"{v}×{key}")

    print("=" * 60)
    print(f"📊 GUI Task Report: {state['task']}")
    print("=" * 60)
    print(f"⏱  Duration:    {time_str}")
    print(f"🪙 Tokens:      {_fmt(total_start)} → {_fmt(total_end)} (+{_fmt(token_delta)})")
    print(f"   Input:       +{_fmt(input_end - input_start)}")
    print(f"   Output:      +{_fmt(output_end - output_start)}")
    print(f"   Cache read:  +{_fmt(cache_delta)}")
    print(f"🔧 Operations:  {', '.join(ops) if ops else 'none tracked'}")
    if state.get("notes"):
        print(f"📝 Notes:")
        for n in state["notes"]:
            print(f"   - {n}")
    print("=" * 60)

    # Save to log
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_entry = {
        "task": state["task"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_s": round(elapsed, 1),
        "tokens_start": total_start,
        "tokens_end": total_end,
        "tokens_delta": token_delta,
        "input_delta": input_end - input_start,
        "output_delta": output_end - output_start,
        "cache_read_delta": cache_delta,
        "operations": {k: state.get(k, 0) for k in COUNTERS},
        "notes": state.get("notes", []),
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    print(f"💾 Saved to {LOG_FILE}")

    # Cleanup
    STATE_FILE.unlink(missing_ok=True)


def history(args):
    """Show recent task history."""
    if not LOG_FILE.exists():
        print("No task history yet.")
        return
    with open(LOG_FILE) as f:
        lines = f.readlines()
    limit = args.limit if hasattr(args, 'limit') and args.limit else 10
    entries = [json.loads(l) for l in lines[-limit:]]

    print(f"{'Task':<35} {'Duration':>8} {'Tokens Δ':>10} {'Date'}")
    print("-" * 75)
    for e in entries:
        delta = e.get("tokens_delta", e.get("context_delta", 0))
        dur_s = e["duration_s"]
        dur = f"{dur_s:.0f}s" if dur_s < 60 else f"{dur_s/60:.1f}m"
        print(f"{e['task']:<35} {dur:>8} {_fmt(delta):>10} {e['timestamp']}")
    print("-" * 75)
    total_delta = sum(e.get("tokens_delta", e.get("context_delta", 0)) for e in entries)
    total_dur = sum(e["duration_s"] for e in entries)
    dur_str = f"{total_dur:.0f}s" if total_dur < 60 else f"{total_dur/60:.1f}m"
    print(f"{'Total':<35} {dur_str:>8} {_fmt(total_delta):>10}  ({len(entries)} tasks)")


def _fmt(n):
    """Format token count."""
    if n is None:
        return "?"
    if abs(n) < 1000:
        return f"{n}"
    elif abs(n) < 1_000_000:
        return f"{n/1000:.1f}k"
    else:
        return f"{n/1_000_000:.2f}M"


def main():
    parser = argparse.ArgumentParser(description="GUI task tracker (auto token tracking)")
    sub = parser.add_subparsers(dest="command")

    p_start = sub.add_parser("start", help="Begin tracking a task")
    p_start.add_argument("--task", help="Task name")
    p_start.add_argument("--session", help="OpenClaw session key (auto-detected if omitted)")

    p_tick = sub.add_parser("tick", help="Increment a counter")
    p_tick.add_argument("counter", choices=COUNTERS)
    p_tick.add_argument("-n", type=int, default=1)

    p_note = sub.add_parser("note", help="Add a note")
    p_note.add_argument("text")

    p_report = sub.add_parser("report", help="Generate final report")
    p_report.add_argument("--session", help="OpenClaw session key (auto-detected if omitted)")

    p_hist = sub.add_parser("history", help="Show task history")
    p_hist.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()
    if args.command == "start":
        start(args)
    elif args.command == "tick":
        tick(args)
    elif args.command == "note":
        note(args)
    elif args.command == "report":
        report(args)
    elif args.command == "history":
        history(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
