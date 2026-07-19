# 样例目录说明 / Sample layout（NetworkPharmacology）

**参考实现**（DeliveryStandards 目录约定）：

```text
01_样例_sample/
  数据文件/                         # RAW only（TCMSP/疾病库交付表、STRING 缓存等）
  代码文件/
    01_run_sample.R                 # 主流程
    02_run_network_preview.R        # 仅网络预览
    03_regen_hctp_layouts.R         # 刷新 HCTP/PPI 布局图
    结果文件/
      图片文件/                     # 01_韦恩… → 15_网络图…
      数据文件/                     # 编号结果表 / Cytoscape 导出
      报告文件/
  参考_交付原图/                    # 韦恩交付原图（非 raw 输入）
```

- 视觉 recipe **frozen**（路径/编号迁移不改布局配色）
- 规范：`00_基础_Foundation/统一交付规范_DeliveryStandards/文档_docs/样例目录与命名_SampleLayoutNaming.md`

```bash
Rscript 代码文件/01_run_sample.R
```
