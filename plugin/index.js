/**
 * GUI Agency Pack — Platform Detection Plugin
 * 
 * Automatically detects the current platform (macOS/Linux/Windows)
 * and injects relevant GUI tool guidance into the agent's context
 * via the before_prompt_build hook.
 * 
 * This is the "Plugin" part of the Agency Pack:
 * - Deterministic: code decides, model doesn't need to think about it
 * - Automatic: runs every prompt build, no model action needed
 * - Minimal: injects only what's needed for the current platform
 */

import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import os from "node:os";
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

function detectPlatform() {
  const platform = os.platform(); // "darwin" | "linux" | "win32"
  const arch = os.arch();         // "arm64" | "x64"
  
  const tools = {};
  const checkBin = (name) => {
    try {
      execSync(`which ${name}`, { stdio: "ignore" });
      return true;
    } catch { return false; }
  };
  
  if (platform === "darwin") {
    tools.pynput = true; // assume available in gui-agent env
    tools.screencapture = checkBin("screencapture");
    tools.pbcopy = checkBin("pbcopy");
    tools.osascript = checkBin("osascript");
  } else if (platform === "linux") {
    tools.pyautogui = true; // assume available
    tools.xdotool = checkBin("xdotool");
    tools.xclip = checkBin("xclip");
    tools.wmctrl = checkBin("wmctrl");
    tools.scrot = checkBin("scrot");
  }
  
  return { platform, arch, tools };
}

function generateContext(platformInfo, verbose) {
  const { platform, arch, tools } = platformInfo;
  const toolList = Object.entries(tools)
    .filter(([, v]) => v)
    .map(([k]) => k)
    .join(", ");
  
  let ctx = `## GUI Agency Pack — Platform Context\n`;
  
  if (platform === "darwin") {
    ctx += `Platform: macOS (${arch})\n`;
    ctx += `Input: pynput (click_at, paste_text, key_combo)\n`;
    ctx += `Screenshot: screencapture\n`;
    ctx += `Clipboard: pbcopy / pbpaste\n`;
    ctx += `Window: osascript (AppleScript)\n`;
    ctx += `Shortcuts: Cmd+S/W/Q/Z/A, Cmd+L (address bar)\n`;
    ctx += `OCR: Apple Vision (detect_text)\n`;
    ctx += `Coordinates: Retina 2x scaling — use detect_to_click()\n`;
  } else if (platform === "linux") {
    ctx += `Platform: Linux (${arch})\n`;
    ctx += `Input: ${tools.xdotool ? 'xdotool type / xdotool key' : 'pyautogui.typewrite / pyautogui.click'}\n`;
    ctx += `Mouse: pyautogui.click(x, y)\n`;
    ctx += `Clipboard: ${tools.xclip ? 'xclip -selection clipboard' : 'xsel --clipboard'}\n`;
    ctx += `Window: ${tools.wmctrl ? 'wmctrl -a "title" / wmctrl -c "title"' : 'xdotool search --name'}\n`;
    ctx += `Shortcuts: Ctrl+S/W/Q/Z/A, Ctrl+Alt+T (terminal)\n`;
    ctx += `OCR: Run on host machine (download screenshot first)\n`;
    ctx += `Coordinates: 1:1 (no Retina scaling)\n`;
    ctx += `Numbers in LibreOffice: prefix with apostrophe ('28208580) to keep as text\n`;
  } else if (platform === "win32") {
    ctx += `Platform: Windows (${arch})\n`;
    ctx += `Input: pyautogui\n`;
    ctx += `Shortcuts: Ctrl+S/W/Z/A\n`;
  }
  
  ctx += `Available tools: ${toolList}\n`;
  
  if (verbose) {
    // Load full platform guide
    const guideMap = { darwin: "macos.md", linux: "linux.md", win32: "windows.md" };
    const guideName = guideMap[platform];
    if (guideName) {
      const guidePath = path.join(path.dirname(import.meta.url.replace("file://", "")), "..", "platforms", guideName);
      try {
        const guide = fs.readFileSync(guidePath, "utf-8");
        ctx += `\n---\n\n${guide}`;
      } catch {}
    }
  }
  
  return ctx;
}

export default definePluginEntry({
  id: "gui-platform-detect",
  name: "GUI Platform Detection",
  description: "Auto-detects platform and injects GUI tool guidance",
  register(api) {
    const verbose = api.pluginConfig?.verbose ?? false;
    
    api.on("before_prompt_build", async ({ prompt, messages }) => {
      // Only inject if gui-agent skill is loaded (available in prompt)
      const hasGuiSkill = prompt && /gui-agent/i.test(prompt);
      if (!hasGuiSkill) {
        return {};  // No GUI skill loaded → don't inject platform context
      }
      
      const platformInfo = detectPlatform();
      const context = generateContext(platformInfo, verbose);
      api.logger.debug(`GUI Platform: ${platformInfo.platform} (${platformInfo.arch}) — injecting context`);
      return { prependSystemContext: context };
    });
    
    api.logger.info("GUI Platform Detection plugin registered");
  },
});
