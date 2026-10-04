"""Nest GenKI outputs as subtype / algorithm / knockout gene and compare with the control gene."""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\10540\Desktop\琪乐无穷\虚拟敲除\结果文件")
ALGORITHM = "GenKI"
CONTROLS = {"PEP": "Abcc8", "NF1": "Gm15551"}
SOURCES = {"PEP": ROOT / "正式_pep_nf1_PEP", "NF1": ROOT / "正式_pep_nf1_NF1"}


def response_genes(path: Path, exclude: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame = frame[frame["gene"].astype(str) != exclude].copy()
    return frame


def go_terms(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=["ID", "Description"])
    frame = pd.read_csv(path)
    if frame.empty or "ID" not in frame.columns:
        return pd.DataFrame(columns=["ID", "Description"])
    return frame


def main() -> None:
    summaries = []
    for subtype, source in SOURCES.items():
        control = CONTROLS[subtype]
        destination = ROOT / subtype / ALGORITHM
        destination.mkdir(parents=True, exist_ok=True)
        for item in source.iterdir():
            target = destination / item.name
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            shutil.move(str(item), str(target))
        if source.exists():
            source.rmdir()

        control_path = destination / control / "响应基因_Responsive.csv"
        control_frame = response_genes(control_path, control) if control_path.exists() else pd.DataFrame(columns=["gene"])
        control_set = set(control_frame["gene"].astype(str))
        control_go = go_terms(destination / control / "富集_GOBP.csv")
        control_go_ids = set(control_go["ID"].astype(str)) if not control_go.empty else set()

        for gene_dir in sorted(path for path in destination.iterdir() if path.is_dir() and path.name not in {"GRNs"}):
            gene = gene_dir.name
            responsive = gene_dir / "响应基因_Responsive.csv"
            if not responsive.exists():
                continue
            partners = response_genes(responsive, gene)
            partner_set = set(partners["gene"].astype(str))
            shared = sorted(partner_set & control_set)
            only_ko = sorted(partner_set - control_set)
            only_control = sorted(control_set - partner_set)
            ko_go = go_terms(gene_dir / "富集_GOBP.csv")
            ko_ids = set(ko_go["ID"].astype(str)) if not ko_go.empty else set()
            shared_ids = sorted(ko_ids & control_go_ids)
            descriptions = {}
            if not ko_go.empty:
                descriptions.update(dict(zip(ko_go["ID"].astype(str), ko_go["Description"].astype(str))))
            if not control_go.empty:
                descriptions.update(dict(zip(control_go["ID"].astype(str), control_go["Description"].astype(str))))
            role = "control" if gene == control else "knockout"
            compare = pd.DataFrame(
                {
                    "subtype": subtype,
                    "algorithm": ALGORITHM,
                    "knockout_gene": gene,
                    "role": role,
                    "control_gene": control,
                    "gene": sorted(partner_set | control_set),
                }
            )
            if compare.empty:
                compare = pd.DataFrame(
                    columns=["subtype", "algorithm", "knockout_gene", "role", "control_gene", "gene", "in_knockout", "in_control", "KL", "hit", "rank"]
                )
            else:
                compare["in_knockout"] = compare["gene"].isin(partner_set)
                compare["in_control"] = compare["gene"].isin(control_set)
                kl = partners.set_index("gene") if not partners.empty else pd.DataFrame()
                if not kl.empty:
                    compare = compare.merge(
                        kl[["KL", "hit", "rank"]],
                        left_on="gene",
                        right_index=True,
                        how="left",
                    )
            compare.to_csv(gene_dir / "与对照比较_VsControl.csv", index=False)
            summaries.append(
                {
                    "subtype": subtype,
                    "algorithm": ALGORITHM,
                    "knockout_gene": gene,
                    "role": role,
                    "control_gene": control,
                    "n_response_excluding_self": len(partner_set),
                    "n_control_excluding_self": len(control_set),
                    "n_shared_genes": len(shared),
                    "genes_only_knockout": ";".join(only_ko),
                    "genes_shared": ";".join(shared),
                    "n_go_knockout": len(ko_ids),
                    "n_go_shared_with_control": len(shared_ids),
                    "shared_go": ";".join(f"{item}|{descriptions.get(item, '')}" for item in shared_ids),
                }
            )
        pd.DataFrame(summaries).query("subtype == @subtype").to_csv(
            destination / "对照对比_ControlCompare.csv", index=False
        )
        (destination / "对照基因.txt").write_text(
            f"subtype={subtype}\nalgorithm={ALGORITHM}\ncontrol_gene={control}\n",
            encoding="utf-8",
        )
    pd.DataFrame(summaries).to_csv(ROOT / "对照对比_PEP_NF1_GenKI.csv", index=False)
    print("NESTED_DONE")


if __name__ == "__main__":
    main()
