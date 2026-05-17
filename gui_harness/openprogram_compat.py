"""Compatibility boundary for the OpenProgram dependency.

GUI Agent Harness only needs three OpenProgram concepts:
- ``agentic_function`` for execution tracing and runtime injection
- ``create_runtime`` for provider setup
- a readable action catalog string for planner prompts

Keep OpenProgram internals out of the rest of the harness so provider and
package refactors in OpenProgram do not force matching changes here.
"""

from __future__ import annotations

import importlib
import types
from typing import Callable

from openprogram import agentic_function


def _load_create_runtime() -> Callable:
    candidates = (
        "openprogram",
        "openprogram.providers",
        "openprogram.legacy_providers",
    )
    errors: list[str] = []

    for module_name in candidates:
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            errors.append(f"{module_name}: {exc}")
            continue

        create = getattr(module, "create_runtime", None)
        if callable(create):
            return create
        errors.append(f"{module_name}: create_runtime missing")

    details = "; ".join(errors)
    raise ImportError(f"No compatible OpenProgram create_runtime found. {details}")


def create_runtime(provider: str | None = None, model: str | None = None, **kwargs):
    """Create an OpenProgram runtime without binding to one provider module path."""
    create = _load_create_runtime()
    if model:
        kwargs["model"] = model
    runtime = create(provider=provider, **kwargs)
    _disable_default_openprogram_tools(runtime)
    return runtime


def _disable_default_openprogram_tools(runtime) -> None:
    """Keep GUI Harness LLM calls text-only unless a caller opts into tools.

    Newer OpenProgram runtimes expose built-in coding tools by default when
    tools is omitted. GUI Harness already owns desktop actions through its
    action registry, so planner/locator/verification calls should not receive
    OpenProgram bash/read/write tools implicitly.
    """
    exec_fn = getattr(runtime, "exec", None)
    if not callable(exec_fn) or getattr(runtime, "_gui_harness_tools_wrapped", False):
        return

    def exec_without_default_tools(self, *args, **exec_kwargs):
        if "tools" in exec_kwargs and exec_kwargs["tools"] is not None:
            return exec_fn(*args, **exec_kwargs)

        # Runtime.exec currently only publishes _current_tools when the value
        # is truthy, so passing tools=[] alone is not enough to suppress the
        # provider default tools. Set the ContextVar around the call instead.
        runtime_mod = importlib.import_module("openprogram.agentic_programming.runtime")
        token = runtime_mod._current_tools.set([])
        try:
            return exec_fn(*args, **exec_kwargs)
        finally:
            runtime_mod._current_tools.reset(token)

    runtime.exec = types.MethodType(exec_without_default_tools, runtime)
    runtime._gui_harness_tools_wrapped = True


def build_action_catalog(available: dict) -> str:
    """Build the planner-visible action catalog from a function registry.

    Only parameters marked ``source="llm"`` are shown. Context-filled values
    such as screenshot path, app name, and runtime stay hidden.
    """
    lines: list[str] = []

    for name, spec in available.items():
        description = spec.get("description", "")
        input_spec = spec.get("input", {})

        llm_params: list[str] = []
        param_details: list[str] = []
        for param_name, param_info in input_spec.items():
            if param_info.get("source") != "llm":
                continue

            type_obj = param_info.get("type", str)
            type_name = getattr(type_obj, "__name__", None) or str(type_obj)
            llm_params.append(f"{param_name}: {type_name}")

            detail = f"    {param_name}"
            if param_info.get("description"):
                detail += f": {param_info['description']}"
            options = param_info.get("options")
            if options:
                option_text = ", ".join(f'"{value}"' for value in options)
                detail += f" (options: {option_text})"
            param_details.append(detail)

        signature = f"{name}({', '.join(llm_params)})" if llm_params else f"{name}()"
        lines.append(signature)

        if description:
            lines.append(f"    {description}")
        lines.extend(param_details)

        if llm_params:
            example_args = ", ".join(
                f'"{param.split(":")[0].strip()}": "..."' for param in llm_params
            )
            lines.append(f'    call: {{"call": "{name}", "args": {{{example_args}}}}}')
        else:
            lines.append(f'    call: {{"call": "{name}"}}')
        lines.append("")

    return "\n".join(lines)
