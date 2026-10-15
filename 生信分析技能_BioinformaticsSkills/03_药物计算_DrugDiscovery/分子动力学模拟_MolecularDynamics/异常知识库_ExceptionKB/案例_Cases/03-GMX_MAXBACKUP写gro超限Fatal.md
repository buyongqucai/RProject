# mdrun 报 Fatal/NaN — GMX_MAXBACKUP 写 gro 超限（非物理）

- 日期/体系：2026-10-10；MMP9/ADA_A2 等分块生产
- 状态：已解决 + 已自动化（prune + 自动续跑）

## 症状（怎么发现的）
监控 NaN 扫描报 `md.log after Started mdrun contains NaN/Fatal`；但温度/势能正常、轨迹完整。

## 判定（真异常还是假象）
看 md.log Fatal 附近 20 行：`Won't make more than N backups of md.gro` / `GMX_MAXBACKUP` ⇒ **备份上限 Fatal，非物理故障**（chunk 循环反复写 md.gro 所致）。
真 NaN/Fatal 特征：Lincs warning 风暴、势能发散、`Segmentation fault`。

## 补救（按序尝试）
1. `rm -f '#md.gro.'*`，`export GMX_MAXBACKUP=-1`（或 5 以内），从 md.cpt 续跑。
2. 已自动化：`运行复合物MD_runComplexMd.sh` 每块前 `prune_md_gro_backups`，块末 Fatal 时 `is_gro_backup_fatal` 判定后自动清备份续跑（轨迹/cpt 不动）。

## 何时放弃
Fatal 与 gro 备份无关且势能发散 ⇒ 物理坏了：查拓扑/约束/初态碰撞，重建体系。

## 复盘
根因：GROMACS 默认 MAXBACKUP=99 与分块写 gro 冲突。预防：脚本默认 `GMX_MAXBACKUP=-1`，块前清理。
