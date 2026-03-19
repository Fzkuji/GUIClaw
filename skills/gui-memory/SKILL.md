---
name: gui-memory
description: "Manage GUIClaw's visual memory — app profiles, components, page fingerprints, state transitions. Create, update, query, and clean up memory entries."
---

# Memory — Visual Knowledge Store

All learned UI knowledge is stored on disk. Memory is what makes GUIClaw able to recognize and operate apps without re-learning every time.

## Directory Structure

```
memory/
├── apps/<appname>/
│   ├── profile.json        # Component registry + page/region/overlay structure
│   ├── summary.json        # App overview (name, description, common tasks)
│   ├── components/         # Cropped component images (PNG, ~30×30 to ~200×200)
│   ├── pages/              # Annotated full-page screenshots
│   └── workflows/          # Saved step sequences for this app
├── meta_workflows/         # Cross-app orchestration sequences
└── sites/<domain>/         # Per-website memory for browsers
    ├── profile.json
    ├── components/
    └── pages/
```

## Profile Structure (profile.json)

```json
{
  "app": "AppName",
  "window_size": [w, h],
  "pages": {
    "main": {
      "fingerprint": { "expect_text": ["Chat", "Cowork"] },
      "regions": {
        "sidebar": { "position": "left", "stable": true, "components": ["Search"] }
      },
      "transitions": { "Cmd+,": { "to": "settings" } }
    }
  },
  "overlays": {
    "menu": { "trigger": "profile_area", "dismiss": ["Esc"] }
  },
  "components": {
    "Search": { "type": "icon", "rel_x": 116, "rel_y": 144, "page": "main" }
  }
}
```

## Key Concepts

| Concept | Description |
|---------|------------|
| **Page** | Full UI state, mutually exclusive (main, settings) |
| **Region** | Area within a page (sidebar, toolbar, content) |
| **Overlay** | Temporary popup over a page (menu, dialog) |
| **Fingerprint** | Text list to identify current page via OCR matching |
| **Transition** | State change triggered by click/key (e.g., Cmd+, → settings) |
| **Component** | A saved UI element image + its relative position |

## Operations

### Create (during learn)

1. `agent.py learn --app AppName` → detects all components, saves to `memory/apps/<appname>/`
2. Creates `profile.json` with component positions, page fingerprints
3. Saves cropped component images to `components/`
4. Saves annotated screenshot to `pages/`

### Query (during detect/click)

1. `agent.py detect --app AppName` → template matches saved components against current screenshot
2. Returns matched components with confidence scores and positions
3. Page identification: OCR current screen → match against page fingerprints

### Update (incremental learn)

When match rate < 80% or new page discovered:
1. `agent.py learn --app AppName --page PageName` → learns specific page
2. Existing pages preserved, new page added
3. New components merged, duplicates removed (similarity > 0.92)

### Delete / Cleanup

```bash
# Remove dynamic content (timestamps, messages, etc.)
python3 scripts/agent.py cleanup --app AppName

# Manual removal of specific component
rm memory/apps/<appname>/components/<ComponentName>.png
# Then update profile.json to remove the entry
```

### Rename Components

```bash
python3 scripts/app_memory.py rename --old old_name --new new_name
```

## Memory Rules

1. **Filename = content**: `chat_button.png`, NOT `icon_0_170_103.png`
2. **Dedup**: similarity > 0.92 = duplicate → keep ONE
3. **Per-app, per-page**: each app has its own directory
4. **Storage hygiene**: DELETE temporary/dynamic content (timestamps, chat messages, notification counts) to prevent storage bloat. No privacy filtering needed — data stays local, never uploaded.
5. **Stability test**: "Same place, same appearance tomorrow?" → KEEP. Otherwise → REMOVE

## Browser Per-Site Memory

Browsers have two layers — app chrome is fixed, each website has different content:

```
memory/apps/google_chrome/
├── profile.json, components/   # Browser chrome (learn once)
└── sites/<domain>/             # Per-website memory
    ├── profile.json, components/, pages/
```

**Save per site**: nav bars, menus, search boxes, filter controls, login buttons, logos
**Don't save**: search results, article content, prices, ads, user-generated content

## What to KEEP vs REMOVE

**KEEP**: sidebar nav icons, toolbar buttons, input controls, window controls, tab headers, fixed logos

**REMOVE**: chat messages, timestamps, user avatars in lists, notification badges, contact names, web content, text >15 chars in content area, profile pictures
