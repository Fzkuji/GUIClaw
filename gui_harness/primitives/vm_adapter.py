"""
gui_harness.primitives.vm_adapter — VM-based backend for GUI primitives.

Monkey-patches the primitives to work with a remote VM via HTTP API
instead of local macOS operations.

Usage:
    from gui_harness.primitives.vm_adapter import patch_for_vm
    patch_for_vm("http://172.16.105.128:5000")
"""

from __future__ import annotations

import base64
import os
import requests
import time

_VM_URL: str | None = None


def patch_for_vm(vm_url: str):
    """Monkey-patch all primitives to use the VM HTTP API."""
    global _VM_URL
    _VM_URL = vm_url.rstrip("/")

    import gui_harness.primitives.screenshot as _ss
    import gui_harness.primitives.input as _inp

    # Patch screenshot
    _ss.take = vm_screenshot
    _ss.take_window = lambda app, out=None: vm_screenshot(out or "/tmp/gui_agent_screen.png")

    # Patch input functions
    _inp.mouse_click = vm_mouse_click
    _inp.mouse_double_click = vm_mouse_double_click
    _inp.mouse_right_click = vm_mouse_right_click
    _inp.key_press = vm_key_press
    _inp.key_combo = vm_key_combo
    _inp.type_text = vm_type_text
    _inp.paste_text = vm_paste_text
    _inp.get_frontmost_app = lambda: "VM Desktop"


def _vm_exec(command: str, timeout: int = 30) -> dict:
    """Execute a command on the VM."""
    r = requests.post(f"{_VM_URL}/execute", json={"command": command}, timeout=timeout)
    return r.json()


def vm_screenshot(path: str = "/tmp/gui_agent_screen.png") -> str:
    """Take a screenshot from the VM and save locally."""
    r = requests.get(f"{_VM_URL}/screenshot", timeout=15)
    with open(path, "wb") as f:
        f.write(r.content)
    return path


def vm_mouse_click(x: int, y: int, button: str = "left", clicks: int = 1):
    btn = "left" if button == "left" else "right"
    cmd = f"python3 -c \"import pyautogui; pyautogui.click({x}, {y}, button='{btn}', clicks={clicks})\""
    _vm_exec(cmd)
    time.sleep(0.3)


def vm_mouse_double_click(x: int, y: int):
    vm_mouse_click(x, y, clicks=2)


def vm_mouse_right_click(x: int, y: int):
    vm_mouse_click(x, y, button="right")


def vm_key_press(key_name: str):
    cmd = f"python3 -c \"import pyautogui; pyautogui.press('{key_name}')\""
    _vm_exec(cmd)
    time.sleep(0.2)


def vm_key_combo(*keys: str):
    key_list = "', '".join(keys)
    cmd = f"python3 -c \"import pyautogui; pyautogui.hotkey('{key_list}')\""
    _vm_exec(cmd)
    time.sleep(0.3)


def vm_type_text(text: str):
    """Type text via pyautogui on the VM.

    Uses pyautogui.write() for simple alphanumeric text.
    Falls back to character-by-character input for special characters.
    """
    b64 = base64.b64encode(text.encode()).decode()
    # Use a script that handles special chars properly
    cmd = (
        f"python3 -c \""
        f"import base64,pyautogui,time; "
        f"t=base64.b64decode('{b64}').decode(); "
        f"pyautogui.write(t, interval=0.02) if t.isalnum() else "
        f"[pyautogui.press(c) if c.isalnum() or c in '.-_' else "
        f"pyautogui.hotkey('shift','9') if c=='(' else "
        f"pyautogui.hotkey('shift','0') if c==')' else "
        f"pyautogui.hotkey('shift',';') if c==':' else "
        f"pyautogui.press('minus') if c=='-' else "
        f"pyautogui.press('space') if c==' ' else "
        f"pyautogui.hotkey('shift','1') if c=='!' else "
        f"pyautogui.hotkey('shift','/') if c=='?' else "
        f"pyautogui.hotkey('shift','2') if c=='@' else "
        f"pyautogui.hotkey('shift',\"'\"  ) if c=='\\\"' else "
        f"pyautogui.press(c) "
        f"for c in t]"
        f"\""
    )
    _vm_exec(cmd)
    time.sleep(0.3)


def vm_paste_text(text: str):
    """Paste text via clipboard on the VM.

    Writes text to a temp file, pipes to xclip/xsel if available,
    otherwise falls back to pyperclip or character-by-character typing.
    """
    b64 = base64.b64encode(text.encode()).decode()
    # Try multiple clipboard methods, fall back to typing
    cmd = (
        f"python3 -c \""
        f"import base64,subprocess,os,pyautogui,time; "
        f"t=base64.b64decode('{b64}').decode(); "
        f"f='/tmp/_vm_clip.txt'; "
        f"open(f,'w').write(t); "
        f"ok=False; "
        f"[ok:=True for _ in [0] if not ok and subprocess.run('xclip -selection clipboard < '+f,shell=True).returncode==0]; "
        f"[ok:=True for _ in [0] if not ok and subprocess.run('xsel --clipboard --input < '+f,shell=True).returncode==0]; "
        f"exec('try:\\n import pyperclip; pyperclip.copy(t); ok=True\\nexcept: pass') if not ok else None; "
        f"pyautogui.hotkey('ctrl','v') if ok else None; "
        f"time.sleep(0.3)"
        f"\""
    )
    result = _vm_exec(cmd)
    # If clipboard paste failed, fall back to typing
    if result.get("error"):
        vm_type_text(text)
