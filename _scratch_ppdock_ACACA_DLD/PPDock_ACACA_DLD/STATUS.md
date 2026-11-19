# PPDock ACACA × DLD — 状态

## 调研定链

见 `01_clean/chain_survey.md`（ST=ACACA/6G2D:C；PT=DLD/6I4Q:A,B）

## 三站

| 服务器 | 状态 |
|--------|------|
| ZDOCK | 已提交（残基约束）；等邮件 |
| ClusPro | Job 1479041 |
| **HDOCK** | **完成**；交付在 `HDOCK_序号文件夹/`（一构象一数字夹） |

## HDOCK 交付布局（对齐分子对接序号金标）

```text
HDOCK_序号文件夹/
  1/ 2/ 3/                 # Top3：结构 + .pse + 图片/ 同夹
  00_服务器原始包_ServerRaw/
  summary_hdock_scores.tsv
  文件夹内容说明.txt
```

主图：`HDOCK_序号文件夹/1/图片/big-1.png`（score −277.53）

**桌面审核包：** `C:\Users\10540\Desktop\ACACA_DLD_蛋白蛋白对接_序号文件夹\`（1/2/3 在根下）

定稿下一步：手调 `1/detail-1.pse` → detail PNG → `图片/result_1.png`
