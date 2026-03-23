const { execSync } = require("child_process");
const { existsSync } = require("fs");
const { join } = require("path");

const TRACKER_STATE = join(
  process.env.HOME || "~",
  ".openclaw/workspace/skills/gui-agent/skills/gui-report/scripts/.tracker_state.json"
);

const TRACKER_SCRIPT = join(
  process.env.HOME || "~",
  ".openclaw/workspace/skills/gui-agent/skills/gui-report/scripts/tracker.py"
);

const PYTHON = join(process.env.HOME || "~", "gui-actor-env/bin/python3");

module.exports = function register(api) {
  api.on("agent_end", (_event, _ctx) => {
    // Only run if tracker has active state (a GUI task was tracked)
    if (!existsSync(TRACKER_STATE)) {
      return;
    }

    try {
      // Read state to check if there's real activity
      const state = JSON.parse(require("fs").readFileSync(TRACKER_STATE, "utf-8"));
      const hasActivity = [
        "screenshots", "clicks", "learns", "transitions",
        "image_calls", "ocr_calls", "detector_calls",
        "workflow_level0", "workflow_level1", "workflow_level2",
        "workflow_auto_steps", "workflow_explore_steps",
      ].some((k) => (state[k] || 0) > 0);

      if (!hasActivity) {
        return;
      }

      // Run report (saves to log + cleans state)
      const pythonBin = existsSync(PYTHON) ? PYTHON : "python3";
      execSync(`${pythonBin} "${TRACKER_SCRIPT}" report`, {
        timeout: 10000,
        stdio: "ignore",
      });
    } catch (_e) {
      // Best-effort — never break the agent
    }
  });
};
