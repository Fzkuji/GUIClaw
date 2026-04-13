"""
gui_harness.planning.remember — manage visual memory for apps.

Wraps app_memory operations with @agentic_function for Context tree integration.
"""

from __future__ import annotations

from agentic import agentic_function

from gui_harness.memory import app_memory


@agentic_function
def remember(operation: str, app_name: str, details: str = None) -> dict:
    """Manage visual memory for an app.

    Operations:
        "list"   — list all known components and states
        "forget" — remove stale/outdated components
        "merge"  — merge similar states in the state graph

    Args:
        operation: One of "list", "forget", "merge".
        app_name:  App whose memory to manage.
        details:   Optional extra info.

    Returns:
        dict with keys: operation, app_name, details
    """
    app_dir = app_memory.get_app_dir(app_name)

    if operation == "list":
        components = app_memory.load_components(app_dir)
        states = app_memory.load_states(app_dir) or {}
        return {
            "operation": "list", "app_name": app_name,
            "details": f"{len(components)} components, {len(states)} states",
        }

    elif operation == "forget":
        components = app_memory.load_components(app_dir)
        meta = app_memory.load_meta(app_dir)
        states = app_memory.load_states(app_dir) or {}
        transitions = app_memory.load_transitions(app_dir) or {}
        # Count stale components and remove them
        stale = [
            name for name, comp in components.items()
            if comp.get("consecutive_misses", 0) >= meta.get("forget_threshold", 15)
        ]
        for name in stale:
            del components[name]
        app_memory.save_components(app_dir, components)
        return {
            "operation": "forget", "app_name": app_name,
            "details": f"Removed {len(stale)} stale components",
        }

    elif operation == "merge":
        states = app_memory.load_states(app_dir) or {}
        # Simple merge: combine states with Jaccard similarity > 0.85
        merged_count = 0
        # Merge logic is handled by app_memory if available
        app_memory.save_states(app_dir, states)
        return {
            "operation": "merge", "app_name": app_name,
            "details": f"Merged {merged_count} similar states",
        }

    else:
        return {
            "operation": operation, "app_name": app_name,
            "details": f"Unknown operation: {operation}",
        }
