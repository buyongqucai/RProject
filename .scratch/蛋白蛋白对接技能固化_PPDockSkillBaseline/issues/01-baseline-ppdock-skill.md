# 01: 固化蛋白蛋白对接技能基线

**类别:** enhancement  
**标签:** 已完成  
**完成日期:** 2026-11-02  
**Blocked by:** None

**What to build:** Agent 仅凭 `技能说明_蛋白蛋白对接_ProteinProteinDocking.md` 即可按基线完成：调研定链 → 清理 → HDOCK（或登记替代）→ 序号文件夹交付 → ST/PT 可视化 → 手调 detail → 切方 → result 拼图。

- [x] `文档_docs/对接与交付基线_PPDockBaseline.md` 存在（状态 BASELINE，可调优）
- [x] SOP / PyMOL / 工具链 / 脚本 README 与基线一致（无 `03_poses`/`04_pymol` 矛盾）
- [x] 入口技能说明 ≤~120 行，只留指针
- [x] 脚本：`prepare_detail_square.py` + `combine_pp_result.py` 可跑说明
- [x] ExceptionKB 索引含 detail 白边案例
- [x] 样例 README 指向桌面序号文件夹金标

## Notes

用户：「如果知道蛋白对接怎么做，可以先固化为技能，后面我再调优」→ BASELINE 非硬 FROZEN。调优改 `对接与交付基线_PPDockBaseline.md` §4。
