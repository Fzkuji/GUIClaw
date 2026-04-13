"""
observe — screenshot + OCR + detection + LLM analysis.

Session mode: summarize={"depth": 0, "siblings": 0}
"""

from __future__ import annotations

from gui_harness.utils import parse_json

from agentic import agentic_function
from gui_harness.perception import screenshot, ocr, detector
from gui_harness.action.input import get_frontmost_app


@agentic_function(summarize={"depth": 0, "siblings": 0})
def observe(task: str, app_name: str = None, runtime=None) -> dict:
    """Observe the current screen state. Analyze the screenshot and detection data.

    You will receive:
    - A screenshot of the current screen
    - OCR text detection results with click-space coordinates
    - UI element detection results with click-space coordinates

    Your job:
    - Describe what page/state the app is in
    - List visible text and interactive elements
    - Determine if the target (from the task) is visible
    - If visible, report its exact coordinates from the detection data

    IMPORTANT: coordinates MUST come from the OCR/detector lists, never estimated.

    Return JSON:
    {
      "app_name": "...",
      "page_description": "short description of current page/state",
      "visible_text": ["key", "text", "labels"],
      "interactive_elements": ["clickable", "element", "names"],
      "target_visible": true/false,
      "target_location": {"x": 0, "y": 0, "label": "..."} or null,
      "screenshot_path": "..."
    }
    """
    if runtime is None:
        raise ValueError("observe() requires a runtime argument")
    rt = runtime

    if not app_name:
        app_name = get_frontmost_app()

    img_path = screenshot.take()
    ocr_results = ocr.detect_text(img_path)

    try:
        _, _, merged, _, _ = detector.detect_all(img_path)
        elements = merged
    except Exception:
        elements = ocr_results

    ocr_lines = "\n".join(
        f"  '{el.get('label', '')}' at ({el.get('cx', 0)}, {el.get('cy', 0)})"
        for el in ocr_results[:60]
    )
    det_lines = "\n".join(
        f"  [{el.get('label', 'UI')}] at ({el.get('cx', 0)}, {el.get('cy', 0)}) "
        f"size={el.get('w', 0)}x{el.get('h', 0)} conf={el.get('confidence', 0):.2f}"
        for el in elements[:50]
    )

    context = f"""Task: {task}
App: {app_name}

OCR text (click-space coordinates):
{ocr_lines or '(none)'}

Detected UI elements (click-space coordinates):
{det_lines or '(none)'}"""

    reply = rt.exec(content=[
        {"type": "text", "text": context},
        {"type": "image", "path": img_path},
    ])

    try:
        result = parse_json(reply)
        result.setdefault("app_name", app_name)
        result.setdefault("screenshot_path", img_path)
        result.setdefault("target_visible", False)
        result.setdefault("target_location", None)
    except Exception:
        result = {
            "app_name": app_name,
            "page_description": reply[:300],
            "visible_text": [el.get("label", "") for el in ocr_results[:10]],
            "interactive_elements": [],
            "target_visible": False,
            "target_location": None,
            "screenshot_path": img_path,
        }

    return result
