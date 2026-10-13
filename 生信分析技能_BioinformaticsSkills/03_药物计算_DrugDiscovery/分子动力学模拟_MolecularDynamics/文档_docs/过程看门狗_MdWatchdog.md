# 过程看门狗 MD-WATCHDOG-v1（稳定版）

> **版本：** `MD-WATCHDOG-v1`（2026-10-12）  
> **地位：** 与块间物理监控（`过程监控_monitorMdRun.sh`）**并列**，不替代。  
> **实现：** [`环境安装_EnvSetup/watchdogMdRun.sh`](../环境安装_EnvSetup/watchdogMdRun.sh)（联接 `E:\md_kit\watchdogMdRun.sh`）  
> **告警：** 仍走 `notify_md_alert.sh` → `E:\alert_kit\`（QQ）。

## 1. 为什么要两层

| 层 | 脚本 | 何时跑 | 管什么 |
|----|------|--------|--------|
| **A 物理块检** | `过程监控_monitorMdRun.sh` | 每个 1 ns chunk **结束后** | 飞出 / RMSD / 温度 / NaN；走 `abort()` |
| **B 过程看门狗** | `watchdogMdRun.sh` | **并行常驻**，按 `POLL_SEC` 轮询 | 进程死没死、轨迹时间还涨不涨；死了读日志归类发信 |

A 管「模拟物理坏了」；B 管「进程没了 / 卡住了但 A 还没机会跑」（例如 `mdrun` Fatal + `set -e` 退出）。  
**错误原因：** GROMACS 是进程 **非 0 退出 + Fatal 文本**，不是 Python `raise`。看门狗把 `mdrun_md.log` / `md.log` / `ABORT_REASON.txt` 尾部归类后写入告警正文。

## 2. v1 稳定策略（刻意保守）

1. **只告警，不自动续跑**（续跑 / `GMX_MAXBACKUP` 清备份属主脚本职责，已在 `运行复合物MD_runComplexMd.sh`）。  
2. **判活优先看 `gmx mdrun`**，其次看 `runComplexMd` / `PID_FILE`。  
3. **进度**只信 `md.log` 最后一行有效 `Step Time`（单位 ps → ns）。  
4. **停滞**：进程仍在，但 `Time` 在 `STALL_MIN` 分钟内不增加 → `STALLED`，发信一次。  
5. **异常死亡**：无 `mdrun`、未达 `TARGET_NS`、无合格 `DONE.txt` → `DEAD_ERROR`，发信一次。  
6. **正常结束**：`DONE.txt` 存在且 `done_ns ≥ TARGET_NS * 0.99`，或时间已达标且无 mdrun → `COMPLETE`，看门狗退出 0（默认不发成功信）。  
7. **去重**：同一 `REASON` 键只发一次（`monitor/ALERT_SENT.txt`）。  
8. **心跳文件**：每轮写 `monitor/heartbeat.json`（外部只读此文件即可知是否在跑）。

## 3. 状态机

```
RUNNING ──stall──► STALLED (alert)
   │
   ├─ process gone + incomplete ──► DEAD_ERROR (alert, exit 1)
   └─ target reached / DONE.txt ──► COMPLETE (exit 0)
```

## 4. 用法

```bash
source ~/activate-md.sh
# 与主 MD 并行（另开 nohup）
nohup bash /mnt/e/md_kit/watchdogMdRun.sh \
  /path/to/workdir \
  --target-ns 100 \
  --pid-file ~/md_runs/logs/job.pid \
  > ~/md_runs/logs/watchdog_job.log 2>&1 &
```

| 环境变量 / 参数 | 默认 | 说明 |
|-----------------|------|------|
| `WORKDIR` / `$1` | 必填 | MD 工作目录 |
| `--target-ns` / `TARGET_NS` | 100 | 目标 ns |
| `--poll-sec` / `POLL_SEC` | 120 | 轮询间隔 |
| `--stall-min` / `STALL_MIN` | 20 | 无时间推进判停滞 |
| `--pid-file` / `PID_FILE` | 空 | 主脚本壳 PID 文件（可选） |
| `SUCCESS_MAIL` | 0 | 1=完成也发 QQ |

只读状态：

```bash
bash /mnt/e/md_kit/md_status.sh /path/to/workdir
# 或直接看 workdir/monitor/heartbeat.json
```

## 5. 归类键（告警 REASON 前缀）

| 前缀 | 含义 |
|------|------|
| `WATCHDOG_STALLED` | 进程在，轨迹时间不涨 |
| `WATCHDOG_DEAD_BACKUP` | 死于 `GMX_MAXBACKUP` / md.gro 备份 |
| `WATCHDOG_DEAD_MDRUN` | 其它 mdrun Fatal / 非 0 |
| `WATCHDOG_DEAD_MONITOR` | 已有 `ABORT_REASON.txt`（物理监控已停） |
| `WATCHDOG_DEAD_UNKNOWN` | 进程没了但日志不足以归类 |

## 6. 非目标（v1 不做）

- 不代替 Origin 出图 / PlotQA  
- 不自动 `nohup` 续跑主脚本（避免双实例抢 `md.cpt`）  
- 不解析 GPU 驱动健康（可在 v2 加）
