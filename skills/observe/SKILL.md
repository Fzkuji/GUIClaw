---
name: gui-observe
description: "Observe current screen state before any GUI action. Screenshot, OCR, identify app/page/state, detect blocking dialogs."
---

# Observe — Know Before You Act

Before ANY GUI task, observe the current state. Do not assume anything from last time.

## Steps

1. **Record baseline** — call `session_status`, note context size for later reporting
2. **Screenshot the target window**:
   ```bash
   python3 scripts/agent.py read_screen --app AppName
   ```
3. **Assess state**:
   - What app is in the foreground? Is the target app visible?
   - What page/state is the app in? (match against known fingerprints)
   - Any popups, dialogs, overlays blocking?
4. **Decide**: proceed to act, or need to dismiss/navigate first?

## Coordinate System

- **Screen**: top-left origin (0,0), logical pixels (Retina physical ÷ scale factor)
- **Window**: relative to window's top-left corner
- **Retina**: screenshots may be 2x+ physical pixels; compute scale dynamically (`screenshot_px / window_logical_px`)
- **cliclick**: uses screen logical pixels, integer only
- **Formula**: `screen_x = window_x + (retina_x / scale_x)`, `screen_y = window_y + (retina_y / scale_y)`

## Window Management

```bash
# Get window bounds
osascript -e 'tell application "System Events" to tell process "AppName" to return {position, size} of window 1'

# Get window ID (uses Swift CGWindowListCopyWindowInfo — see ui_detector.py)

# Capture specific window only
screencapture -x -l <windowID> output.png

# Activate app
osascript -e 'tell application "AppName" to activate'
```

## Page Identification

1. OCR the screen → get visible text
2. Match against known page fingerprints in profile.json
3. Identify current page (main, settings, etc.)
4. Only match components belonging to that page

## Detection Stack

| Detector | Finds | Speed | Best for |
|----------|-------|-------|----------|
| **Template Match** | Previously seen components | 0.3s | Known elements (conf ≈ 1.0) |
| **GPA-GUI-Detector (YOLO)** | Icons, buttons, UI elements | 0.3s | Unknown buttons/controls |
| **Apple Vision OCR** | Text (Chinese + English) | 1.6s | Labels, menus, content |
