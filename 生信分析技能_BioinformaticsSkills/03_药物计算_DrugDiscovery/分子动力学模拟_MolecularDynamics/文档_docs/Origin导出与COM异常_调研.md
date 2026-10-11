# Origin 导出与 COM 异常捕获（调研）

> 日期：2026-10-10  
> 触发：出图时反复出现 `TYPE.ERRORS` / 轴范围异常，脚本仍报 OK。

## 1. 能否接到 Origin 抛出的异常？

| 通道 | 能力 | 局限 |
|------|------|------|
| `Application.Execute(script)` 返回值 | **Boolean**：False=该段 LabTalk 失败（[官方 Execute](https://docs.originlab.com/com/classes/application/execute/)） | 部分「属性设置错误」仍可能弹 UI，返回值不一定可靠 |
| COM `try/catch` | 捕获 ProgID / 进程级 COM 异常 | **接不到** Origin 内部 LabTalk 属性对话框 |
| LabTalk `vErr` + `{ ... }` + `@NOE=0` | 官方 Error Handling：出错跳到 `}`，`vErr` 保持 1；`@NOE=0` 关闭错误弹窗（[Error Handling](https://docs.originlab.com/labtalk/guide/error-handling/)、[FAQ-363 @NOE](https://docs.originlab.com/quick-help/change-target-window-for-error/)） | soft 命令（如 `label -r Legend` 不存在）也会置 `vErr`，需白名单 |
| `LTVar` / `LTStr` | 读回 LabTalk 变量（如 `vErr`） | 无「GetLastError 字符串」API |

**结论：** 能部分捕获。正确做法是：

1. 会话开始 `@NOE = 0`（抑弹窗）  
2. 每条 Hard LabTalk 用 `{ cmd; vErr=0 }` 包装，读 `LTVar('vErr')`  
3. `Execute==False` 或 `vErr==1` → **判失败**；有 hardFail 时**不得**因 PNG 存在而报 OK  
4. Soft 行（删 legend）失败可忽略  

此前脚本只看「有没有 PNG」，因此你看到 Error 弹窗时日志仍写 `OK`。

## 2. 数据如何正确导出（SSOT）

金标导出在样例 R：`01_样例_sample/代码文件/02_分析出图_plotMdAnalysis.R`（约 L448–465）。  
生产捷径：`脚本_scripts/导出Origin数据_exportMdOriginCsv.py`（须与 R 列名/单位一致）。

### 2.1 单位（最易错）

GROMACS xvg 的 `@ xaxis label` 可能是 **ps 或 ns**，不能一律 `/1000`：

| 文件 | 常见单位 | 导出 |
|------|----------|------|
| `rmsd_*.xvg`（`-tu ns`） | ns | 原样 → `time_ns` |
| `sasa.xvg`（`-tu ns`） | ns | 原样 |
| `gyrate.xvg`（默认） | **ps** | `/1000` → `time_ns`（R：`time_ps/1000`） |
| `energy_*.xvg` | **ps** | `/1000` |
| `hbond_num.xvg` | 常为 ps | `/1000`；列 `n_hbond`（第 2 列） |
| `rmsf_calpha.xvg` | residue | 不转时间 |

解析策略：读 `@ xaxis label`；含 `(ps)` 或 `max(t)>500` 则 `/1000`。

### 2.2 列名契约（Origin `prepare_inputs`）

| CSV | 列 |
|-----|-----|
| `RMSD_backbone.csv` | `time_ns,rmsd_nm` |
| `RMSD_protein_ligand_complex.csv` | 长表 `time_ns,series,rmsd_nm`（series∈Protein/Ligand/Complex） |
| `RMSF_calpha.csv` | `residue,rmsf_nm` |
| `HBonds_protein_ligand.csv` | `time_ns,n_hbond` |
| `Rg.csv` | `time_ns,rg_nm` |
| `SASA.csv` | `time_ns,sasa_nm2` |
| `COM_distance.csv` | `time_ns,dist_nm` |
| `NVT_temperature.csv` | `time_ns,temp_K` |
| `NPT_equilibration.csv` | `time_ns,temp_K,press_bar,density` |
| `MD_potential.csv` | `time_ns,pot_kj` |
| FEL | `x,y,dg_kj` |

### 2.3 本次实测缺口与修复（MMP9 / ADA）

- `rmsd_complex`：索引组名是 `Protein_LIG`，且常**重名**；按名选 Fatal → 改为解析**组号**再 `gmx rms`  
- `hbond`：GROMACS 2024 新 `gmx hbond` 对 GAFF 配体报无 D/A → 改用 **`gmx hbond-legacy`**  
- `gyrate` / `energy_*`：ps→ns（读 `@ xaxis label`）  
- COM：`Execute` + `vErr`/`@NOE`；FEL 装饰行（`ColorScale1.title$`、`hide_fel_contours`）标 soft，不删图  

## 3. 代码改动指针

- COM 失败即失败：`origin出图_plotMdOrigin.py` → `_ps_one_plot` / `run_one_plot`  
- 导出单位与 Complex：`导出Origin数据_exportMdOriginCsv.py`  
- 补算入口：`环境安装_EnvSetup/run_extra_then_export.sh` + `补算必备分析_extraMdAnalysis.sh`
