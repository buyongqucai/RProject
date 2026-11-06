# 影刀 CLI 接入整个项目

**标签:** 已完成

让 RProject 用影刀 CLI 跑已有的疾病/药物 RPA，而不是只覆盖 Linux/信创命令。拖入影刀应用目录时，一并使用 `package.json` 里 `kind: Code` 的 Python 指令。

SSOT：`.cursor/skills/shadowbot-cli/SKILL.md`。

## 验收

- Windows 走 `shadowbot.shell-cli.exe`，Linux/mac/信创走 `shadowbot-cli`
- 疾病和药物取数指向应用「网络药理学数据建模机器人」
- 拖入项目时，Code 流程的 `.py` 经客户端任务运行；`import xbot` 不丢给系统 Python
