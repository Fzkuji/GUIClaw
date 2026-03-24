# gui-setup 设计文档

> 最后更新：2026-03-24

## 核心目的

一键搭建 GUIClaw 运行环境。用户只需要 `bash scripts/setup.sh`，不需要手动安装任何依赖。

## setup.sh 做的事

1. **系统依赖**：通过 Homebrew 安装 cliclick、Python 3.12
2. **Python 虚拟环境**：创建 `~/gui-agent-env/`
3. **Python 包**：PyTorch、ultralytics（YOLO）、OpenCV、huggingface_hub
4. **GPA-GUI-Detector 模型**：从 HuggingFace 下载到 `~/GPA-GUI-Detector/model.pt`
5. **Memory 目录**：创建 `memory/apps/`
6. **验证**：加载模型确认一切正常

## 设计决策

### 为什么用独立虚拟环境而不是 pip install

GUIClaw 的依赖（PyTorch、ultralytics）很重，和用户的其他 Python 项目可能冲突。独立 venv 隔离依赖。

路径固定为 `~/gui-agent-env/` 而不是项目内的 `.venv`，因为：
- GUIClaw 作为 OpenClaw skill 可能被安装到不同位置
- scripts 里 hardcode 了 `~/gui-agent-env/bin/python3`
- 多个 GUIClaw 实例可以共享同一个 venv

### 为什么模型放在 ~/GPA-GUI-Detector/ 而不是项目内

同理——项目可能在 workspace/skills/gui-agent 下，也可能在其他位置。模型 200MB 不应该被重复下载。

### 辅助功能权限

macOS 要求辅助功能权限才能用 pynput 控制鼠标/键盘。setup.sh 不能自动授权（需要用户在系统设置里手动操作），但会提醒用户。

### OpenClaw 配置推荐

setup.sh 输出推荐的 openclaw.json 配置：
- `exec.timeoutSec: 300` — GUI 操作链可能较长，5 分钟超时推荐
- `queue.mode: "interrupt"` — 用户可以发送任意消息中止当前操作

## 平台限制

当前只支持 macOS Apple Silicon：
- GPA-GUI-Detector 用 PyTorch MPS 加速
- OCR 用 Apple Vision Framework（Swift）
- 鼠标/键盘用 pynput（需要辅助功能权限）

Linux 部分功能可用（GPA 检测、模板匹配），但没有 OCR（需要替换实现）和辅助功能限制。
