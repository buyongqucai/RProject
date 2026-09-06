# 技术路线：AutoSite + AutoDock-GPU（优先）

> **状态：`FROZEN`（2026-09-05 用户确认）** — 细则见 [`对接与交付约束_DockingFrozen.md`](对接与交付约束_DockingFrozen.md)  
> **引擎：** AutoDock-GPU（`E:\AutoDock-GPU\AutoDock-GPU.exe`，AD4 打分）  
> **定盒：** 有共晶 → Meeko enveloping；无共晶 → **AutoSite**  
> **异常回退：** P2Rank → Fpocket(+PRANK) → 文献位点 / `manual`  
> **明确不做：** 共晶配体重对接 + RMSD 自检（非流水线步骤）  
> **结构库：** 优先 `D:\数据库\分子对接数据库`  
> **关联：** [`对接盒子定心与定边_DockingBoxProtocol.md`](对接盒子定心与定边_DockingBoxProtocol.md)、[`分子对接流水线规范_DockingPipelineSOP.md`](分子对接流水线规范_DockingPipelineSOP.md)、[`中心位点方法登记_CenterSourceRegistry.md`](中心位点方法登记_CenterSourceRegistry.md)

---

## 0. 设计原则（第一性）

1. **对接 = 在相互作用有利空间内搜索姿态** → 位点优先用 **能量探针（AutoSite）**，与 AD4/AutoDock-GPU 同生态。  
2. **有共晶仍优先实验位点**（Meeko `--box_enveloping`）；无共晶才主跑 AutoSite。  
3. **单一方法会偏** → AutoSite 结果必须过质控；异常则换几何/ML 口袋交叉验证。  
4. **AD-GPU 与 Vina 分数不可混表**；本路线交付物单独命名（`summary_adgpu.csv` 等）。  
5. **禁止**整链 COM、固定边长 22、全 HETATM 平均中心。

---

## 1. 总流程（强制顺序）

```text
① 取结构（本地库优先）
② 受体清洗：去结晶水/盐离子；保留功能辅因子（如 heme-Fe）并配平
③ 配体：PubChem 3D → PDBQT（Meeko 或现有 clean_h）
④ 定中心/定盒（见 §2 决策树）
⑤ Meeko/ADT：生成 AutoGrid 地图（.maps.fld）
⑥ AutoDock-GPU：默认 --nrun 20（可调）
⑦ 质控：能量为负、姿态是否在盒内、聚类；**不做**共晶 RMSD 重对接  
⑧ 异常任务：换中心方法重定盒 → 重跑地图+GPU（仅失败任务）  
⑨ 登记表 / 矩阵 / PyMOL / 热图（AD-GPU 专档）；detail 手调断点
```

---

## 2. 定中心 / 定盒决策树

```text
有可用共晶小分子配体？
  ├─ 是 → Meeko: --box_enveloping 共晶.pdb --padding 5
  │         center_source=cocrystal_meeko
  │         （AutoSite 可作对照，不默认覆盖共晶）
  └─ 否 → AutoSite Top 位点（主路径）
            ├─ 质控 PASS → 采用 AutoSite 中心 + 盒
            │               center_source=autosite
            └─ 质控 FAIL（§3）→ 回退链：
                  1) P2Rank Top1–3 与 AutoSite 交叉
                  2) 若仍歧义：Fpocket (+PRANK 重打分)
                  3) 文献 / UniProt 注释残基中心
                  4) 仍失败：换 PDB / 人工指定 → 阻塞该靶点
```

**边长（本路线）：**

| 来源 | 规则 |
|------|------|
| Meeko 共晶 | enveloping + **padding=5**；若 query \(L_{\max}\) 更大，扩到至少 \(L_{\max}+2\times5\) |
| AutoSite | 用 AutoSite 推荐包围盒；过紧则按 query \(L_{\max}+10\)（两侧各 5）扩边 |
| 回退 P2Rank/Fpocket | 以预测中心为心，立方边长取 **\(\max(L_{\max}+10,\; 4\times R_g,\; 20)\)**；任一边 \(>30\) 提高 GPU 搜索强度并警告（**不**因 S>40 硬拒） |

---

## 3. AutoSite「异常」质控（触发回退）

任一命中即 `box_qc=FAIL`，进入 §2 回退（可多选对照）：

| ID | 检查 | 异常阈值（工程默认，可调） |
|----|------|----------------------------|
| Q1 | 输出空 / 无可靠 Top 口袋 | 无 |
| Q2 | 中心落在蛋白外或远离表面 | 到最近 Cα \(> 8\,\text{Å}\) 且不在空腔 |
| Q3 | 盒子过大（近盲对接） | 任一边 \(> 35\,\text{Å}\) 或体积 \(> 40000\,\text{Å}^3\) |
| Q4 | 盒子过小装不下 query | 任一边 \(< L_k^{\text{query}}+6\) |
| Q5 | 与功能注释冲突 | 远离已知催化/结合残基（有注释时）\(> 12\,\text{Å}\) |
| Q6 | 多方法不一致 | AutoSite Top1 与 P2Rank Top1 中心距离 \(> 10\,\text{Å}\)（回退时跑 P2Rank） |
| Q7 | 对接后姿态 | best pose 质心明显出盒或严重穿模；AD4 能量异常极端 |

记录：`box_qc=PASS|FAIL`、`fail_codes=Q2,Q6`、`center_source=`、`fallback_used=`。  
**落盘：** 每个任务的 `task_info` 与 `summary_adgpu.csv` 同行必须带合法 `center_source`（词表见 CenterSourceRegistry）；禁止只交能量不交中心方法。

---

## 4. AutoDock-GPU 运行约定

| 项 | 约定 |
|----|------|
| 可执行文件 | `E:\AutoDock-GPU\AutoDock-GPU.exe` |
| 设备 | OpenCL，RTX 4060；`--devnum 1`（多卡再改） |
| 搜索 | 默认 **`--nrun 20`**（LGA runs）；需要更稳可加到 40 |
| 地图 | 每受体（或每盒）一份 `.maps.fld`；**换中心/换盒必须重跑 AutoGrid** |
| 配体 | Meeko `mk_prepare_ligand` 或库内 `*_clean_h.pdbqt`（须与 AD4 原子类型兼容） |
| 输出 | 每任务 `dlg`/`xml` + 提取 best energy → `summary_adgpu.csv` |
| 路径 | Windows 工程目录用 **ASCII**（与 Vina 相同约束） |

示例：

```bat
E:\AutoDock-GPU\AutoDock-GPU.exe ^
  --lfile ligand.pdbqt ^
  --ffile receptor.maps.fld ^
  --nrun 20 ^
  --resnam task01
```

---

## 5. 目录与交付（与 Vina 工程隔离）

```text
<项目根_ASCII>/
  分子对接_蛋白表.csv          # 含 center_source, box_qc, ref_ligand/autosite_rank
  分子对接_化合物表.csv
  maps/                        # *.maps.fld 与 map 文件
  1/ … N/                      # 任务：pdbqt, dlg/xml, log, 图片/
  summary_adgpu.csv            # 禁止与 summary_vina.csv 混用
  矩阵_结合能_ADGPU.csv
  BREAKPOINT_等待手调detail标签.txt
```

桌面可用中文父目录（如 `努力学习`），**对接 cwd 仍须 ASCII 子目录**。

---

## 6. 工具安装清单（本机）

| 工具 | 路径/状态 | 用途 |
|------|-----------|------|
| AutoDock-GPU | `E:\AutoDock-GPU\` ✅ | 对接引擎 |
| AutoSite | **待装到 E:**（如 `E:\AutoSite\`） | 主定盒 |
| Meeko | **待装** | 配体/受体/PDBQT、GPF、共晶 enveloping |
| AutoGrid4 | **待装**（ADT 或 Meeko 流程） | 生成 `.maps.fld` |
| P2Rank / Fpocket | **按需装** | 仅 AutoSite 异常回退 |
| Open Babel / PyMOL | 已有 | 格式与出图 |

---

## 7. 与旧 Vina 批次关系

- 已跑 Vina 结果可保留作对照，**不**自动覆盖。  
- 新课题默认走本路线（AD-GPU）。  
- 正结合能/错盒问题：在本路线下用 §2–§3 重定盒后重跑，不沿用固定 22 + 盲信库表。

---

## 8. 实施里程碑（给 Agent）

1. 安装 AutoSite + Meeko + AutoGrid 到 E:  
2. 写 `批量对接_runBatchAdgpu.py`：决策树 §2 + GPU 调用  
3. 对「努力学习」课题：缺共晶靶点走 AutoSite；FAIL 则 P2Rank/Fpocket  
4. TP53/3d06、FGA 等无共晶：必须过 §3；FGA 禁止链 COM  
5. 出 `summary_adgpu` + 热图；detail 仍在手调断点停  

---

## 9. 一句话路线

**共晶 → Meeko 包盒定心；否则 AutoSite → AutoGrid → AutoDock-GPU（nrun=20）；盒/中心异常再 P2Rank/Fpocket/文献回退。不做共晶 RMSD 重对接验收。**
