#!/usr/bin/env python3
"""GUI task tracker — records baseline and computes deltas for time, tokens, and operations."""

import argparse
import json
import os
import time

STATE_FILE = os.path.join(os.path.dirname(__file__), ".tracker_state.json")


def start(args):
    """Record baseline before a GUI task."""
    state = {
        "task": args.task or "unnamed",
        "start_time": time.time(),
        "tokens_in": args.tokens_in or 0,
        "tokens_out": args.tokens_out or 0,
        "cache_hits": args.cache_hits or 0,
        "screenshots": 0,
        "clicks": 0,
        "learns": 0,
        "detects": 0,
        "image_calls": 0,
        "notes": [],
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print(f"📊 Tracker started: {state['task']}")


def tick(args):
    """Increment a counter (screenshots, clicks, learns, detects, image_calls)."""
    if not os.path.exists(STATE_FILE):
        print("⚠ No active tracker. Call `start` first.")
        return
    with open(STATE_FILE) as f:
        state = json.load(f)
    key = args.counter
    if key not in state:
        print(f"⚠ Unknown counter: {key}")
        return
    state[key] = state.get(key, 0) + (args.n or 1)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print(f"  +{args.n or 1} {key} (total: {state[key]})")


def note(args):
    """Add a free-form note to the current task."""
    if not os.path.exists(STATE_FILE):
        print("⚠ No active tracker.")
        return
    with open(STATE_FILE) as f:
        state = json.load(f)
    state.setdefault("notes", []).append(args.text)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print(f"  📝 Note added")


def report(args):
    """Generate final report with deltas."""
    if not os.path.exists(STATE_FILE):
        print("⚠ No active tracker. Nothing to report.")
        return

    with open(STATE_FILE) as f:
        state = json.load(f)

    elapsed = time.time() - state["start_time"]
    tokens_in_delta = (args.tokens_in or 0) - state["tokens_in"]
    tokens_out_delta = (args.tokens_out or 0) - state["tokens_out"]
    cache_delta = (args.cache_hits or 0) - state["cache_hits"]
    total_tokens = tokens_in_delta + tokens_out_delta + cache_delta

    # Format time
    if elapsed < 60:
        time_str = f"{elapsed:.1f}s"
    elif elapsed < 3600:
        time_str = f"{elapsed/60:.1f}min"
    else:
        time_str = f"{elapsed/3600:.1f}h"

    # Format tokens
    def fmt_tokens(n):
        if abs(n) < 1000:
            return str(n)
        elif abs(n) < 1_000_000:
            return f"{n/1000:.1f}k"
        else:
            return f"{n/1_000_000:.2f}M"

    # Build report
    ops = []
    for key in ["screenshots", "clicks", "learns", "detects", "image_calls"]:
        v = state.get(key, 0)
        if v > 0:
            ops.append(f"{v}×{key}")

    print("=" * 60)
    print(f"📊 GUI Task Report: {state['task']}")
    print("=" * 60)
    print(f"⏱  Duration:    {time_str}")
    print(f"📥 Tokens in:   {fmt_tokens(tokens_in_delta)} (new) + {fmt_tokens(cache_delta)} (cached)")
    print(f"📤 Tokens out:  {fmt_tokens(tokens_out_delta)}")
    print(f"📦 Total:       {fmt_tokens(total_tokens)}")
    print(f"🔧 Operations:  {', '.join(ops) if ops else 'none tracked'}")
    if state.get("notes"):
        print(f"📝 Notes:")
        for n in state["notes"]:
            print(f"   - {n}")
    print("=" * 60)

    # Save report to log
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_entry = {
        "task": state["task"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_s": round(elapsed, 1),
        "tokens_in": tokens_in_delta,
        "tokens_out": tokens_out_delta,
        "cache_hits": cache_delta,
        "total_tokens": total_tokens,
        "operations": {k: state.get(k, 0) for k in ["screenshots", "clicks", "learns", "detects", "image_calls"]},
        "notes": state.get("notes", []),
    }
    log_file = os.path.join(log_dir, "task_history.jsonl")
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    print(f"💾 Saved to {log_file}")

    # Cleanup state
    os.remove(STATE_FILE)


def history(args):
    """Show recent task history."""
    log_file = os.path.join(os.path.dirname(__file__), "..", "logs", "task_history.jsonl")
    if not os.path.exists(log_file):
        print("No task history yet.")
        return
    with open(log_file) as f:
        lines = f.readlines()
    limit = args.limit or 10
    entries = [json.loads(l) for l in lines[-limit:]]

    print(f"{'Task':<30} {'Duration':>10} {'Tokens':>12} {'Date'}")
    print("-" * 70)
    for e in entries:
        total = e.get("total_tokens", e["tokens_in"] + e["tokens_out"] + e.get("cache_hits", 0))
        def fmt(n):
            return f"{n/1000:.1f}k" if abs(n) >= 1000 else str(n)
        dur = f"{e['duration_s']:.0f}s" if e["duration_s"] < 60 else f"{e['duration_s']/60:.1f}m"
        print(f"{e['task']:<30} {dur:>10} {fmt(total):>12} {e['timestamp']}")
    print("-" * 70)
    total_tokens = sum(e.get("total_tokens", e["tokens_in"] + e["tokens_out"] + e.get("cache_hits", 0)) for e in entries)
    def fmt_t(n):
        return f"{n/1000:.1f}k" if abs(n) >= 1000 else str(n)
    print(f"{'Total':>42} {fmt_t(total_tokens):>12}  ({len(entries)} tasks)")


def main():
    parser = argparse.ArgumentParser(description="GUI task tracker")
    sub = parser.add_subparsers(dest="command")

    p_start = sub.add_parser("start", help="Begin tracking a task")
    p_start.add_argument("--task", help="Task name")
    p_start.add_argument("--tokens-in", type=int, help="Current input tokens")
    p_start.add_argument("--tokens-out", type=int, help="Current output tokens")
    p_start.add_argument("--cache-hits", type=int, help="Current cache hit tokens")

    p_tick = sub.add_parser("tick", help="Increment a counter")
    p_tick.add_argument("counter", choices=["screenshots", "clicks", "learns", "detects", "image_calls"])
    p_tick.add_argument("-n", type=int, default=1)

    p_note = sub.add_parser("note", help="Add a note")
    p_note.add_argument("text")

    p_report = sub.add_parser("report", help="Generate final report")
    p_report.add_argument("--tokens-in", type=int, help="Final input tokens")
    p_report.add_argument("--tokens-out", type=int, help="Final output tokens")
    p_report.add_argument("--cache-hits", type=int, help="Final cache hit tokens")

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
