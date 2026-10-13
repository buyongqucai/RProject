# MD 默认生产级（Default Production NS）

标签: 待Agent处理

## 背景

用户确认：说「跑 MD」默认生产级（`NS≥100` + 监控）；仅当明确说「烟测/测试」才用短轨迹。

## 范围

- SSOT：`复合物MD流水线_GromacsSop.md` §9.0
- 入口：`技能说明_分子动力学模拟_MolecularDynamics.md`
- 脚本默认：`运行复合物MD_runComplexMd.sh` / `环境安装_EnvSetup/runComplexMd.sh` 的 `NS` 默认值
