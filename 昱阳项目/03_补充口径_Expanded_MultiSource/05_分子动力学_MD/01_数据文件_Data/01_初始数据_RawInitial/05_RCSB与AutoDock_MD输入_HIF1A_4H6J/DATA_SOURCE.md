# 05_HIF1A_4H6J_Quercetin — MD 初始数据来源

```
data_provenance: REAL
receptor_source: RCSB PDB 4H6J
receptor_prep: clean_protein_for_md.py（去 DNA/RNA、水、结晶添加剂与非目标 HETATM；链 A）
receptor_repair: pdbfixer 1.12（补缺失侧链原子 + 解析 altloc，去氢输出；2026-10-13）
ligand_source: AutoDock-GPU（补充口径对接）
pose: Vina MODEL1 from quercetin_out.pdbqt
```

| 文件 | 说明 |
|------|------|
| `01_PDB_受体_Receptor_4H6J.pdb` | 清理后的受体（MD 用） |
| `02_AutoDock_对接姿态_QuercetinPose_HIF1A.pdbqt` | 槲皮素对接姿态（Vina 原始 pdbqt） |
| `PREP_NOTE.txt` | 上游准备记录（如存在） |

上游指针：`04_分子对接_Docking/`（补充口径对接结果）；配体公共来源 PubChem CID 5280343（槲皮素）。
