# Plugin + Skill 配合原则

## 核心思想

**Plugin 负责确定性环境，Skill 负责开放性决策。**

一个任务的执行可以分为两个阶段：

1. **环境感知阶段**（Plugin 主导）— 确定"我在哪里、我有什么"
2. **任务执行阶段**（Skill 主导）— 决定"我要做什么、怎么做"

模型的认知资源是有限的。在任务开始时，如果让模型同时搞清楚环境和做决策，它会两头都做不好。Plugin 在框架层面自动完成环境感知，模型只需要专注于任务本身。

## 阶段模型

```
任务开始
  │
  ▼
┌─────────────────────────────────┐
│  Phase 1: Plugin（自动、确定性） │
│  ─────────────────────────────  │
│  • 平台检测（OS、工具、显示）    │
│  • 环境注入（prompt 前置内容）   │
│  • 模型不参与决策               │
│  • 目标：让模型"睁开眼就知道     │
│    自己在哪里"                   │
└─────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────┐
│  Phase 2: Skill（开放、自主）    │
│  ─────────────────────────────  │
│  • 视觉检测（截图→OCR→YOLO）    │
│  • 操作决策（点哪里、输什么）    │
│  • 记忆管理（保存/读取组件）     │
│  • 模型自主判断                 │
│  • 目标：让模型"自己决定怎么     │
│    完成任务"                    │
└─────────────────────────────────┘
  │
  ▼
任务完成
```

## 设计原则

### 原则一：早期多 Plugin，后期多 Skill

任务开始时，模型对环境一无所知。这时应该通过 Plugin **自动**提供尽可能多的上下文：
- 当前平台是什么（macOS / Linux / Windows）
- 有哪些工具可用（pynput / pyautogui / xdotool）
- 屏幕分辨率、显示协议（X11 / Wayland / Quartz）
- 键盘快捷键映射（Cmd vs Ctrl）

这些信息通过 `before_prompt_build` hook **自动注入**，模型不需要执行任何命令就已经知道了。

到了任务执行阶段，模型已经了解了环境，这时切换到 Skill 模式——模型自己观察屏幕、做决策、执行操作。Skill 提供的是**方法论**（怎么检测、怎么点击、怎么验证），不是具体指令。

### 原则二：Plugin 处理不该让模型决策的事

有些事情模型**不应该**花时间决策：
- ❌ "我应该用 pynput 还是 pyautogui？" → Plugin 检测后直接告诉它
- ❌ "这台机器有没有 xdotool？" → Plugin 检测后直接告诉它
- ❌ "Ctrl+S 还是 Cmd+S？" → Plugin 根据平台直接给出

这些是**环境事实**，不是**策略选择**。Plugin 处理事实，Skill 处理策略。

### 原则三：Skill 处理需要模型判断力的事

有些事情**必须**由模型决策：
- ✅ "这个按钮在哪里？" → 截图 + OCR + 模型判断
- ✅ "现在应该点击还是输入？" → 模型根据上下文决定
- ✅ "操作失败了，怎么恢复？" → 模型分析错误并调整
- ✅ "这个页面是我期望的吗？" → 模型视觉理解

这些需要**理解力和判断力**，只有模型能做。Skill 提供流程框架（截图→检测→操作→验证），模型在框架内自主决策。

### 原则四：Plugin 的注入要精简

Plugin 注入的内容会占用 context window。注入太多等于浪费 token。

**好的注入：**
```
Platform: Linux (aarch64), X11
Input: xdotool type / pyautogui.click
Clipboard: xclip -selection clipboard
Shortcuts: Ctrl+S (save), Ctrl+W (close), Ctrl+Q (quit)
```

**差的注入：** 把整个 linux.md（100+ 行）塞进 prompt。

Plugin 应该只注入**当前需要的最小信息集**。详细参考放在 Skill 的 references 里，模型需要时自己去读。

### 原则五：随着学习减少依赖

模型在操作过程中会积累经验（GUI memory）。当它已经学会了一个应用的操作模式后：
- Plugin 的环境注入可以更简短（模型已经知道了）
- Skill 的指导可以更少（模型有 memory 可查）
- 模型的自主空间应该更大

这类似于新员工 vs 老员工：
- 新员工需要详细的入职手册（Plugin 多注入）+ 手把手教（Skill 严格流程）
- 老员工只需要简短提醒（Plugin 少注入）+ 自由发挥（Skill 开放流程）

## 具体应用：GUI Agent

### Plugin 层（gui-agent-plugin）

```typescript
// before_prompt_build hook
api.on("before_prompt_build", async () => {
    const platform = detectPlatform();
    const summary = formatPlatformSummary(platform);
    return { prependSystemContext: summary };
});
```

注入内容示例：
```
## GUI Agent — Platform Context
Platform: Linux (aarch64), Display: X11
Input: xdotool (type, key, mousemove+click)
Clipboard: xclip -selection clipboard  
Window: wmctrl -a "title"
Shortcuts: Ctrl+S/W/Q/Z/A, Ctrl+Alt+T (terminal)
OCR: Run on host (macOS), coordinates 1:1 (no Retina scaling)
```

### Skill 层（gui-agent SKILL.md）

模型读了 Skill 后知道：
- 截图→OCR→YOLO 的检测流程
- learn_from_screenshot / record_page_transition 的 memory 管理
- 坐标来源规则（只从检测结果取，不猜）
- 失败恢复策略

但 Skill **不**告诉模型用什么工具打字或点击——这已经由 Plugin 注入了。

## 总结

| 维度 | Plugin | Skill |
|------|--------|-------|
| 执行时机 | 自动（框架调用） | 按需（模型决定读取） |
| 决策者 | 代码逻辑 | 模型智能 |
| 内容类型 | 环境事实 | 操作方法 |
| 变化频率 | 每次启动检测 | 相对稳定 |
| 任务阶段 | 早期（感知环境） | 后期（执行任务） |
| 目标 | 减少模型不必要的决策 | 释放模型的判断力 |
