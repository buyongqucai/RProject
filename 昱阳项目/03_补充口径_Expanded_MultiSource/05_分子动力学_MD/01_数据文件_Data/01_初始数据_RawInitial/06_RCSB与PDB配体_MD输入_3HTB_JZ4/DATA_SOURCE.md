# 3HTB_JZ4_100ns — MD 初始数据来源

```
data_provenance: REAL
receptor_source: RCSB PDB 3HTB
receptor_prep: clean_protein_for_md.py（去 DNA/RNA、水、结晶添加剂与非目标 HETATM；链 A）
ligand_source: RCSB PDB 3HTB 内置配体 JZ4
pose: 3HTB 晶体配体 JZ4
```

| 文件 | 说明 |
|------|------|
| `01_PDB_受体_Receptor_3HTB.pdb` | 清理后的受体（MD 用） |
| `02_PDB_配体_JZ4Ligand.mol2` | 质子化 JZ4 配体 |
| `PREP_NOTE.txt` | 上游准备记录（如存在） |

上游指针：`04_分子对接_Docking/`（补充口径对接结果）；配体公共来源 PubChem CID 5280343（槲皮素）。
