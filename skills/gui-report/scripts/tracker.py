#!/usr/bin/env python3
"""GUI task tracker — fully automatic performance tracking.

Auto-starts on first detect_all() call. Counters auto-tick from app_memory.py.
Report organized by: task → time → cost → operations → navigation efficiency → memory changes.

Usage:
    tracker.py start --task "Task name" [--session SESSION_KEY]
    tracker.py tick COUNTER [-n N]
    tracker.py note "some text"
    tracker.py report [--session SESSION_KEY]
    tracker.py history [--limit N]
"""

import argparse
import json
import time
from pathlib import Path

STATE_FILE = Path(__file__).parent / ".tracker_state.json"
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "task_history.jsonl"
SESSIONS_FILE = Path.home() / ".openclaw" / "agents" / "main" / "sessions" / "sessions.json"

# Memory root for reading component/state changes
MEMORY_ROOT = Path(__file__).parent.parent.parent.parent / "memory" / "apps"

COUNTERS = [
    "screenshots", "clicks", "learns", "transitions",
    "image_calls", "ocr_calls", "detector_calls",
    "workflow_level0", "workflow_level1", "workflow_level2",
    "workflow_auto_steps", "workflow_explore_steps",
    "components_new", "components_forgotten", "states_new", "states_merged",
]


def _find_session_key(preferred=None):
    if preferred:
        return preferred
    if not SESSIONS_FILE.exists():
        return None
    try:
        with open(SESSIONS_FILE) as f:
            sessions = json.load(f)
        best_key, best_time = None, 0
        for key, data in sessions.items():
            if "discord:direct" in key or "main:main" in key:
                updated = data.get("updatedAt", 0)
                if updated > best_time:
                    best_time = updated
                    best_key = key
        return best_key
    except Exception:
        return None


def _read_tokens(session_key=None):
    if not SESSIONS_FILE.exists():
        return None
    try:
        with open(SESSIONS_FILE) as f:
            sessions = json.load(f)
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
    except Exception:
        return None


def _fmt(n):
    if n is None:
        return "?"
    if abs(n) < 1000:
        return f"{n}"
    elif abs(n) < 1_000_000:
        return f"{n/1000:.1f}k"
    else:
        return f"{n/1_000_000:.2f}M"


def _fmt_time(seconds):
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}min"
    else:
        return f"{seconds/3600:.1f}h"


def _read_memory_snapshot():
    """Read current memory stats (component count, state count per app/site)."""
    snapshot = {}
    if not MEMORY_ROOT.exists():
        return snapshot
    try:
        for comp_file in MEMORY_ROOT.rglob("components.json"):
            app_dir = comp_file.parent
            rel = str(app_dir.relative_to(MEMORY_ROOT))
            with open(comp_file) as f:
                comps = json.load(f)
            states_file = app_dir / "states.json"
            states = {}
            if states_file.exists():
                with open(states_file) as f:
                    states = json.load(f)
            trans_file = app_dir / "transitions.json"
            trans = {}
            if trans_file.exists():
                with open(trans_file) as f:
                    trans = json.load(f)
            snapshot[rel] = {
                "components": len(comps),
                "states": len(states),
                "transitions": len(trans),
            }
    except Exception:
        pass
    return snapshot


# ═══════════════════════════════════════════
# Core API
# ═══════════════════════════════════════════

def start(args):
    session = args.session if hasattr(args, 'session') else None
    task = args.task if hasattr(args, 'task') else None

    # Auto-save previous session if exists (failsafe for missed report)
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                old_state = json.load(f)
            # Only save if it had real activity (not just auto-started and abandoned)
            has_activity = any(old_state.get(c, 0) > 0 for c in COUNTERS)
            if has_activity:
                old_tokens = _read_tokens(old_state.get("session_key"))
                _, log_entry = _build_report(old_state, old_tokens, save=True, cleanup=False)
                print(f"  💾 Auto-saved previous session: {old_state.get('task', '?')}")
        except Exception:
            pass

    tokens = _read_tokens(session)
    memory_snapshot = _read_memory_snapshot()

    state = {
        "task": task or "auto",
        "start_time": time.time(),
        "session_key": tokens["sessionKey"] if tokens else None,
        "tokens_start": tokens,
        "memory_start": memory_snapshot,
        "notes": [],
    }
    for c in COUNTERS:
        state[c] = 0

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

    if tokens:
        print(f"📊 Tracker started: {state['task']}")
        print(f"   Session: {tokens['sessionKey']}")
        print(f"   Baseline: {_fmt(tokens['totalTokens'])} total tokens")
    else:
        print(f"📊 Tracker started: {state['task']} (⚠ no session tokens)")


def tick_counter(counter, n=1):
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


def tick(args):
    if not STATE_FILE.exists():
        return
    try:
        key = args.counter if hasattr(args, 'counter') else args
        n = args.n if hasattr(args, 'n') and args.n else 1
        tick_counter(key, n)
    except Exception:
        pass


def update_task_name(name):
    if not STATE_FILE.exists():
        return
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
        if state.get("task") in ("auto", "unnamed"):
            state["task"] = name
            with open(STATE_FILE, "w") as f:
                json.dump(state, f)
    except Exception:
        pass


def note(args):
    if not STATE_FILE.exists():
        return
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
        text = args.text if hasattr(args, 'text') else args
        state.setdefault("notes", []).append(text)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception:
        pass


# ═══════════════════════════════════════════
# Report generation
# ═══════════════════════════════════════════

def _build_report(state, tokens_now, save=False, cleanup=False):
    """Build report data and formatted output.
    
    Returns: (formatted_string, log_entry_dict)
    """
    elapsed = time.time() - state["start_time"]
    tokens_start = state.get("tokens_start") or {}

    # Token deltas
    t_start = tokens_start.get("totalTokens", 0)
    t_end = tokens_now.get("totalTokens", 0) if tokens_now else 0
    t_delta = t_end - t_start
    i_delta = (tokens_now.get("inputTokens", 0) if tokens_now else 0) - tokens_start.get("inputTokens", 0)
    o_delta = (tokens_now.get("outputTokens", 0) if tokens_now else 0) - tokens_start.get("outputTokens", 0)
    c_delta = (tokens_now.get("cacheRead", 0) if tokens_now else 0) - tokens_start.get("cacheRead", 0)

    # Memory changes
    memory_now = _read_memory_snapshot()
    memory_start = state.get("memory_start", {})
    
    total_comps_start = sum(v.get("components", 0) for v in memory_start.values())
    total_comps_now = sum(v.get("components", 0) for v in memory_now.values())
    total_states_start = sum(v.get("states", 0) for v in memory_start.values())
    total_states_now = sum(v.get("states", 0) for v in memory_now.values())
    total_trans_start = sum(v.get("transitions", 0) for v in memory_start.values())
    total_trans_now = sum(v.get("transitions", 0) for v in memory_now.values())

    comp_delta = total_comps_now - total_comps_start
    state_delta = total_states_now - total_states_start
    trans_delta = total_trans_now - total_trans_start

    # Navigation efficiency
    auto_steps = state.get("workflow_auto_steps", 0)
    explore_steps = state.get("workflow_explore_steps", 0)
    total_steps = auto_steps + explore_steps
    auto_rate = (auto_steps / total_steps * 100) if total_steps > 0 else 0

    # Detection stats
    detect_calls = state.get("detector_calls", 0)
    ocr_calls = state.get("ocr_calls", 0)
    image_calls = state.get("image_calls", 0)

    # Build formatted output
    lines = []
    lines.append(f"📊 任务报告：{state['task']}")
    lines.append("━" * 40)
    lines.append("")

    # Time
    lines.append(f"⏱ 耗时：{_fmt_time(elapsed)}")
    lines.append("")

    # Cost
    lines.append(f"💰 Token 消耗：")
    lines.append(f"   总计 +{_fmt(t_delta)} tokens")
    lines.append(f"   input +{_fmt(i_delta)} | output +{_fmt(o_delta)} | cache +{_fmt(c_delta)}")
    lines.append("")

    # Detection
    lines.append(f"🔍 检测：")
    lines.append(f"   detect_all {detect_calls} 次 | OCR {ocr_calls} 次 | LLM 视觉 {image_calls} 次")
    lines.append(f"   组件总量：{total_comps_now}（{'+' if comp_delta >= 0 else ''}{comp_delta}）")
    lines.append("")

    # Operations
    clicks = state.get("clicks", 0)
    transitions = state.get("transitions", 0)
    learns = state.get("learns", 0)
    if clicks or transitions or learns:
        lines.append(f"🖱 操作：")
        parts = []
        if clicks:
            parts.append(f"点击 {clicks} 次")
        if transitions:
            parts.append(f"状态转移 {transitions} 个")
        if learns:
            parts.append(f"学习 {learns} 次")
        lines.append(f"   {' | '.join(parts)}")
        lines.append("")

    # Navigation efficiency
    if total_steps > 0:
        lines.append(f"🗺 导航效率：")
        lines.append(f"   自动模式 {auto_steps} 步 | 探索模式 {explore_steps} 步")
        lines.append(f"   自动率 {auto_rate:.0f}%")
        l0 = state.get("workflow_level0", 0)
        l1 = state.get("workflow_level1", 0)
        l2 = state.get("workflow_level2", 0)
        if l0 or l1 or l2:
            lines.append(f"   验证分布：L0(模板) {l0} | L1(检测) {l1} | L2(LLM) {l2}")
        lines.append("")

    # Memory changes
    if comp_delta or state_delta or trans_delta:
        lines.append(f"📝 记忆变化：")
        if comp_delta:
            lines.append(f"   组件 {'+' if comp_delta > 0 else ''}{comp_delta}（{total_comps_start} → {total_comps_now}）")
        if state_delta:
            lines.append(f"   状态 {'+' if state_delta > 0 else ''}{state_delta}（{total_states_start} → {total_states_now}）")
        if trans_delta:
            lines.append(f"   转移 {'+' if trans_delta > 0 else ''}{trans_delta}（{total_trans_start} → {total_trans_now}）")
        lines.append("")

    # Notes
    if state.get("notes"):
        lines.append(f"📝 备注：")
        for n in state["notes"]:
            lines.append(f"   - {n}")
        lines.append("")

    lines.append("━" * 40)

    formatted = "\n".join(lines)

    # Log entry
    log_entry = {
        "task": state["task"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_s": round(elapsed, 1),
        "tokens_delta": t_delta,
        "input_delta": i_delta,
        "output_delta": o_delta,
        "cache_delta": c_delta,
        "detect_calls": detect_calls,
        "ocr_calls": ocr_calls,
        "image_calls": image_calls,
        "clicks": clicks,
        "transitions": transitions,
        "learns": learns,
        "auto_steps": auto_steps,
        "explore_steps": explore_steps,
        "auto_rate": round(auto_rate, 1),
        "level0": state.get("workflow_level0", 0),
        "level1": state.get("workflow_level1", 0),
        "level2": state.get("workflow_level2", 0),
        "comp_delta": comp_delta,
        "state_delta": state_delta,
        "trans_delta": trans_delta,
        "comp_total": total_comps_now,
        "state_total": total_states_now,
        "trans_total": total_trans_now,
        "notes": state.get("notes", []),
    }

    # Save to log
    if save:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    # Cleanup
    if cleanup and STATE_FILE.exists():
        STATE_FILE.unlink(missing_ok=True)

    return formatted, log_entry


def one_line_summary(state, tokens_now):
    """Generate a one-line report summary."""
    elapsed = time.time() - state.get("start_time", time.time())
    tokens_start = state.get("tokens_start") or {}
    t_delta = (tokens_now.get("totalTokens", 0) if tokens_now else 0) - tokens_start.get("totalTokens", 0)

    detect = state.get("detector_calls", 0)
    clicks = state.get("clicks", 0)
    auto_s = state.get("workflow_auto_steps", 0)
    explore_s = state.get("workflow_explore_steps", 0)

    parts = [f"⏱{_fmt_time(elapsed)}", f"🪙+{_fmt(t_delta)}"]
    if detect:
        parts.append(f"🔍{detect}")
    if clicks:
        parts.append(f"🖱{clicks}")
    if auto_s or explore_s:
        total = auto_s + explore_s
        rate = int(auto_s / total * 100) if total else 0
        parts.append(f"🗺auto:{rate}%")

    return "📊 " + " | ".join(parts)


LAST_REPORT_FILE = Path(__file__).parent / ".last_report.txt"


def auto_report():
    """Generate inline report string. Does NOT save or cleanup."""
    if not STATE_FILE.exists():
        return "⚠ No active tracker."
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
        tokens_now = _read_tokens(state.get("session_key"))
        formatted, _ = _build_report(state, tokens_now, save=False, cleanup=False)
        return formatted
    except Exception as e:
        return f"⚠ auto_report failed: {e}"


def report(args):
    """Generate final report, save to log, save one-line summary, cleanup state."""
    if not STATE_FILE.exists():
        print("⚠ No active tracker.")
        return
    with open(STATE_FILE) as f:
        state = json.load(f)
    session = args.session if hasattr(args, 'session') else None
    tokens_now = _read_tokens(state.get("session_key") or session)
    formatted, log_entry = _build_report(state, tokens_now, save=True, cleanup=True)

    # Save one-line summary for next detect_all to display
    try:
        summary = one_line_summary(state, tokens_now)
        with open(LAST_REPORT_FILE, "w") as f:
            f.write(summary)
    except Exception:
        pass


def history(args):
    if not LOG_FILE.exists():
        print("No task history yet.")
        return
    with open(LOG_FILE) as f:
        lines = f.readlines()
    limit = args.limit if hasattr(args, 'limit') and args.limit else 10
    entries = [json.loads(l) for l in lines[-limit:]]

    print(f"{'Task':<30} {'Time':>6} {'Tokens':>8} {'Clicks':>6} {'Auto%':>5} {'Comps':>6} {'Date'}")
    print("─" * 85)
    for e in entries:
        dur = _fmt_time(e["duration_s"])
        tokens = f"+{_fmt(e.get('tokens_delta', 0))}"
        clicks = e.get("clicks", 0)
        auto_rate = f"{e.get('auto_rate', 0):.0f}%"
        comp_delta = e.get("comp_delta", 0)
        comps = f"{'+' if comp_delta >= 0 else ''}{comp_delta}"
        print(f"{e['task']:<30} {dur:>6} {tokens:>8} {clicks:>6} {auto_rate:>5} {comps:>6}  {e['timestamp']}")
    print("─" * 85)
    total_tokens = sum(e.get("tokens_delta", 0) for e in entries)
    total_dur = sum(e["duration_s"] for e in entries)
    total_clicks = sum(e.get("clicks", 0) for e in entries)
    print(f"{'合计':<30} {_fmt_time(total_dur):>6} {'+' + _fmt(total_tokens):>8} {total_clicks:>6} {'':>5} {'':>6}  ({len(entries)} tasks)")


def main():
    parser = argparse.ArgumentParser(description="GUI task tracker")
    sub = parser.add_subparsers(dest="command")

    p_start = sub.add_parser("start")
    p_start.add_argument("--task")
    p_start.add_argument("--session")

    p_tick = sub.add_parser("tick")
    p_tick.add_argument("counter", choices=COUNTERS)
    p_tick.add_argument("-n", type=int, default=1)

    p_note = sub.add_parser("note")
    p_note.add_argument("text")

    p_report = sub.add_parser("report")
    p_report.add_argument("--session")

    p_hist = sub.add_parser("history")
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
