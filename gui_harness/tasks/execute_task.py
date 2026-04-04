"""
execute_task — the main planning loop.

Takes a natural language task and autonomously loops:
  observe → plan → act → verify → repeat

This is the single entry point. SKILL.md points here.

Note: execute_task is NOT an @agentic_function because it orchestrates
multiple sub-functions that each call exec() once. The agentic runtime
enforces one exec() per @agentic_function, so the orchestrator must be
a plain function.
"""

from __future__ import annotations

import json

from agentic import agentic_function

_runtime = None


def _get_runtime():
    global _runtime
    if _runtime is None:
        from gui_harness.runtime import GUIRuntime
        _runtime = GUIRuntime()
    return _runtime


@agentic_function(summarize={"depth": 0, "siblings": 0})
def plan_next_action(task: str, obs: dict, step: int, max_steps: int,
                     history: list, runtime=None) -> dict:
    """Ask the LLM to decide the next action based on current observation.

    Returns dict with: action, target, text, reasoning
    """
    rt = runtime or _get_runtime()

    history_summary = ""
    if history:
        lines = []
        for h in history[-5:]:  # Last 5 actions
            status = "✅" if h.get("success") else "❌"
            target_str = str(h.get('target', ''))[:40]
            lines.append(f"  {h['step']}. {status} {h['action']} → {target_str}")
        history_summary = f"\nRecent actions:\n" + "\n".join(lines)

    prompt = f"""Task: {task}

Current screen state:
  App: {obs.get('app_name', 'unknown')}
  Description: {obs.get('page_description', 'unknown')}
  Visible text: {obs.get('visible_text', [])[:20]}
  Interactive elements: {obs.get('interactive_elements', [])[:15]}
  Target visible: {obs.get('target_visible', False)}
  Target location: {obs.get('target_location')}

Step {step}/{max_steps}.{history_summary}

What is the single next action to take? Return JSON:
{{
  "action": "click" or "type" or "double_click" or "right_click" or "shortcut" or "key_press" or "done",
  "target": "what to click/interact with",
  "text": "text to type (only for type action)",
  "reasoning": "why this action"
}}

Return "done" as action if the task is already completed."""

    reply = rt.exec(content=[
        {"type": "text", "text": prompt},
    ])

    try:
        return _parse_json(reply)
    except Exception:
        return {"action": "done", "reasoning": f"Could not parse plan: {reply[:200]}"}


def execute_task(task: str, runtime=None, max_steps: int = 15) -> dict:
    """Execute a GUI task autonomously.

    Runs an observe → plan → act → verify loop until the task is complete
    or max_steps is reached.

    This is a plain function (not @agentic_function) because it orchestrates
    multiple sub-functions that each use exec() once.

    Args:
        task:       Natural language description of what to do.
        runtime:    Optional: GUIRuntime instance.
        max_steps:  Maximum number of actions (default: 15).

    Returns:
        dict with keys:
            task (str)
            success (bool)
            steps_taken (int)
            final_state (str)
            history (list[dict])  — each step's action + result
    """
    from gui_harness.functions.observe import observe
    from gui_harness.functions.act import act

    rt = runtime or _get_runtime()

    history = []
    completed = False

    for step in range(max_steps):
        # 1. OBSERVE — what's on screen now?
        obs = observe(
            task=f"Step {step + 1}/{max_steps}. Task: {task}. What is the current state? What should I do next?",
            runtime=rt,
        )

        # 2. PLAN — ask LLM what action to take (separate @agentic_function)
        plan = plan_next_action(
            task=task, obs=obs, step=step + 1, max_steps=max_steps,
            history=history, runtime=rt,
        )

        action = plan.get("action", "done")

        # 3. CHECK — is the task done?
        if action == "done":
            completed = True
            history.append({"step": step + 1, "action": "done", "reasoning": plan.get("reasoning", "")})
            break

        # 4. ACT — execute the planned action
        if action == "key_press":
            from gui_harness.primitives import input as _input
            _input.key_press(plan.get("target", "return"))
            act_result = {"action": "key_press", "target": plan.get("target"), "success": True, "screen_changed": True}
        elif action == "shortcut":
            from gui_harness.primitives import input as _input
            keys = [k.strip() for k in plan.get("target", "").split("+")]
            _input.key_combo(*keys)
            act_result = {"action": "shortcut", "target": plan.get("target"), "success": True, "screen_changed": True}
        else:
            act_result = act(
                action=action,
                target=plan.get("target", ""),
                text=plan.get("text"),
                runtime=rt,
            )

        history.append({
            "step": step + 1,
            "action": action,
            "target": plan.get("target", ""),
            "text": plan.get("text"),
            "reasoning": plan.get("reasoning", ""),
            "success": act_result.get("success", False),
            "screen_changed": act_result.get("screen_changed", False),
        })

    # Final verification
    final_obs = observe(task=f"Task was: {task}. Is it completed?", runtime=rt)

    return {
        "task": task,
        "success": completed,
        "steps_taken": len(history),
        "final_state": final_obs.get("page_description", "unknown"),
        "history": history,
    }


def _parse_json(reply: str) -> dict:
    text = reply.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return json.loads(text)
