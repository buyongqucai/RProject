# 07 — .gitignore 卫生

标签: 待Agent处理

## 来源

Standards 轴（卫生项）。

## 问题

根 `.gitignore` 未覆盖 `__pycache__/`、`Rplots.pdf`（当前以未跟踪出现）。

## 验收标准

- 根 `.gitignore` 增加 `__pycache__/`、`Rplots.pdf`、`*.pyc`；
- `git status` 不再出现这两类未跟踪项。
