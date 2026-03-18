---
name: gui-browser
description: "Operate browsers visually — navigate URLs, interact with web pages, manage per-site visual memory. Two-layer system: browser chrome + web content."
---

# Browser — Two-Layer Visual Memory

Browsers are a two-layer system — same app, different content per site:

1. **Browser chrome** (tabs, address bar, bookmarks) — fixed, learn once
2. **Web page content** — different per site, need per-site memory

## Memory Structure

```
memory/apps/google_chrome/
├── profile.json          # Browser chrome UI
├── components/           # Browser UI icons
└── sites/                # Per-website memory
    ├── 12306.cn/
    │   ├── profile.json  # Site-specific elements
    │   ├── components/   # Site buttons, nav
    │   └── pages/
    └── google.com/
```

## Navigation

Navigate visually — activate Chrome, focus address bar, paste URL, Enter:

```bash
python3 scripts/agent.py navigate --url "https://example.com"
```

Under the hood: Cmd+L → paste URL → Enter. Uses the current window and profile.

## Operation Flow

1. Learn browser chrome once → address bar, tab controls, etc.
2. Navigate: Cmd+L → paste URL → Enter
3. New website: wait for load → detect page content area → save fixed site UI
4. Operate: template match site elements → OCR text → click

## Per-Site Memory

**Save**: navigation bars, menus, search boxes, filter/sort controls, login buttons, logos

**Don't save**: search results, article content, prices, ads, user-generated content

## Input Quirks

- **Autocomplete fields** (e.g., 12306 stations): typing alone is NOT enough — must click the dropdown suggestion
- **Chinese input**: System IME interferes with autocomplete. Switch to English, type pinyin, let website autocomplete handle it
- **Cmd+V in forms**: May garble text. Use `cliclick t:text` for ASCII/pinyin
- **Date pickers**: Usually need calendar UI clicks, not typed dates
