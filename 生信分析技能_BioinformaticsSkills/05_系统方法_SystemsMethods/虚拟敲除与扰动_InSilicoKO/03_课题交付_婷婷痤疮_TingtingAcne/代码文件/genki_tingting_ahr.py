# -*- coding: utf-8 -*-
"""婷婷痤疮：皮损 TREM2 macrophage × AHR 的 GenKI 正式跑。

协议对齐琪乐无穷 GenKI（Yang NAR 2023）：HVG3000、top15% 边、100 次搜索、
1000 次不放回排列、KL top5% 且 hit>95%。富集用人源。
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
import traceback
from pathlib import Path

DESKTOP = Path(r"C:\Users\10540\Desktop\婷婷\虚拟敲除")
CODE = Path(__file__).resolve().parent
CPLX_GENKI = Path(
    r"E:\RProject\生信分析技能_BioinformaticsSkills\05_系统方法_SystemsMethods"
    r"\虚拟敲除与扰动_InSilicoKO\02_课题交付_Cplx2Control\GenKI_GenKI\代码文件"
)
RSCRIPT = Path(r"E:\R-4.6.0\bin\Rscript.exe")
EXPORT_R = CODE / "01_导出GenKI输入_ExportGenKiMtx.R"
ENRICH_R = CODE / "04_人源富集_EnrichHuman.R"

PRIMARY = "AHR"
KNOCK_GENES = (PRIMARY,)
SEED = 8096
N_HVG = 3000
EDGE_PERCENTILE = 85
N_TRIALS = 100
MAX_EPOCHS = 100
N_PERMUTATIONS = 1000

# CLI：python genki_tingting_ahr.py ["TREM2 macrophage"| "M2-like macrophage"] [run_id]
import sys as _sys

SUBTYPE = _sys.argv[1] if len(_sys.argv) >= 2 else "TREM2 macrophage"
RUN_ID = _sys.argv[2] if len(_sys.argv) >= 3 else "tingting_ahr"

RESULT_DIR = DESKTOP / "结果文件" / "_跨亚群" / "GenKI" / "报告文件"
OUT_ROOT = DESKTOP / "结果文件" / SUBTYPE / "GenKI"
RUN_LOG = RESULT_DIR / f"正式运行日志_{RUN_ID}.log"
PROGRESS_JSON = RESULT_DIR / f"进度_状态_{RUN_ID}.json"
PROGRESS_TXT = RESULT_DIR / f"进度_Progress_{RUN_ID}.txt"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def log_line(msg: str) -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{time.strftime('%H:%M:%S')}  {msg}\n"
    with RUN_LOG.open("a", encoding="utf-8") as fh:
        fh.write(line)
    print(line, end="", flush=True)


def update_progress(text: str, headline: str | None = None) -> None:
    state = {"headline": headline or "GenKI 婷婷 AHR", "slots": {"当前阶段": text}}
    if PROGRESS_JSON.exists():
        try:
            old = json.loads(PROGRESS_JSON.read_text(encoding="utf-8"))
            state["slots"] = old.get("slots", {})
            state["slots"]["当前阶段"] = text
            if headline:
                state["headline"] = headline
        except Exception:
            pass
    PROGRESS_JSON.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    PROGRESS_TXT.write_text(
        (state["headline"] + "\n\n当前阶段  " + text + "\n\n完整日志: " + str(RUN_LOG) + "\n"),
        encoding="utf-8",
    )


def export_mtx() -> None:
    completed = subprocess.run(
        [str(RSCRIPT), str(EXPORT_R), SUBTYPE],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout)[-2000:])
    log_line((completed.stdout or "").strip().splitlines()[-1] if completed.stdout else "export ok")


def main() -> int:
    sys.path.insert(0, str(CPLX_GENKI))
    # CpuCap must load before torch in workers; load here for plan only
    cap = load_module("genki_cpucap", CPLX_GENKI / "00_资源上限_CpuCap.py")
    gf = load_module("genki_formal", CPLX_GENKI / "genki_formal.py")

    # Patch formal module for this project
    gf.DESKTOP = DESKTOP
    gf.RESULT_DIR = RESULT_DIR
    gf.RUN_ID = RUN_ID
    gf.PROGRESS_JSON = PROGRESS_JSON
    gf.PROGRESS_TXT = PROGRESS_TXT
    gf.RUN_LOG = RUN_LOG
    gf.TARGET = PRIMARY
    gf.KNOCK_GENES = KNOCK_GENES
    gf.SUBTYPES = (SUBTYPE,)
    gf.N_HVG = N_HVG
    gf.EDGE_PERCENTILE = EDGE_PERCENTILE
    gf.N_TRIALS = N_TRIALS
    gf.MAX_EPOCHS = MAX_EPOCHS
    gf.N_PERMUTATIONS = N_PERMUTATIONS
    gf.SEED = SEED
    gf.log_line = log_line
    gf.update_progress = lambda key, text, headline=None: update_progress(text, headline)

    def choose_control_ahr(selected):
        import numpy as np

        matrix = selected.layers["norm"]
        if hasattr(matrix, "toarray"):
            matrix = matrix.toarray()
        names = list(selected.var_names)
        if PRIMARY not in names:
            raise RuntimeError("AHR missing after HVG")
        anchor = matrix[:, names.index(PRIMARY)]
        banned = set(KNOCK_GENES)
        best_name, best_r = None, None
        for index, name in enumerate(names):
            if name in banned or float(np.std(matrix[:, index])) == 0.0:
                continue
            corr = float(np.corrcoef(matrix[:, index], anchor)[0, 1])
            if np.isnan(corr):
                continue
            if best_r is None or abs(corr) < abs(best_r):
                best_name, best_r = name, corr
        if best_name is None:
            raise RuntimeError("no control gene")
        return best_name, best_r

    gf.choose_control = choose_control_ahr

    def enrich_human(gene_csv: Path, out_csv: Path, knockout: str = "") -> str:
        out_dir = Path(out_csv).parent
        completed = subprocess.run(
            [str(RSCRIPT), str(ENRICH_R), str(gene_csv), str(out_dir), knockout or PRIMARY],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        msg = (completed.stdout or "") + (completed.stderr or "")
        if completed.returncode != 0:
            return "enrichment failed: " + msg[-500:]
        return msg.strip().splitlines()[-1] if msg.strip() else "enrich ok"

    gf.enrich_response = enrich_human

    # Patch run_subtype internals that require Cplx2 presence
    original_run = gf.run_subtype

    def run_subtype_ahr(cap_mod, subtype: str, search_workers: int, out_dir=None) -> None:
        import numpy as np
        import pandas as pd
        import torch
        from concurrent.futures import ProcessPoolExecutor, as_completed
        from GenKI.dataLoader import DataLoader

        out_root = Path(out_dir) if out_dir is not None else DESKTOP / "结果文件" / subtype / "GenKI"
        wt_data = out_root / "_野生型" / "数据文件"
        wt_report = out_root / "_野生型" / "报告文件"
        done_flag = out_root / "FORMAL_DONE.txt"
        if done_flag.exists():
            log_line(f"{subtype} 已有正式结果，跳过")
            return
        out_root.mkdir(parents=True, exist_ok=True)
        wt_data.mkdir(parents=True, exist_ok=True)
        wt_report.mkdir(parents=True, exist_ok=True)
        started = time.time()
        update_progress(f"{subtype} 建网", headline=f"GenKI {subtype} AHR")
        present = gf.detected_knock_genes(subtype)
        if not present:
            log_line(f"{subtype} AHR 不可敲，停止")
            return
        selected, forced = gf.prepare_adata(subtype, [g for g, _ in present])
        selected.write_h5ad(wt_data / f"hvg3000.h5ad")
        log_line(f"{subtype} HVG cells={selected.n_obs} genes={selected.n_vars} forced={forced}")
        wrapper = DataLoader(
            selected,
            target_gene=[PRIMARY],
            GRN_file_dir=str(wt_data / "GRNs"),
            rebuild_GRN=True,
            cutoff=EDGE_PERCENTILE,
            n_cpus=int(cap_mod.prepare("grn", bind_device=False)["grn"]["workers"]),
        )
        data_wt = wrapper.load_data()
        try:
            import ray

            if ray.is_initialized():
                ray.shutdown()
        except Exception:
            pass
        graph_path = wt_data / "wt_graph.npz"
        np.savez(graph_path, x=data_wt.x.numpy(), edge_index=data_wt.edge_index.numpy())
        (wt_data / "genes.txt").write_text("\n".join(map(str, data_wt.y)) + "\n", encoding="utf-8")
        log_line(f"{subtype} 建网完成 边 {int(data_wt.edge_index.shape[1])}")

        rng = np.random.default_rng(SEED)
        tasks = []
        for trial in range(N_TRIALS):
            tasks.append(
                {
                    "trial": trial,
                    "subtype": subtype,
                    "n_trials": N_TRIALS,
                    "graph_npz": str(graph_path),
                    "lr": gf.draw_hyper(rng, -4, -1),
                    "beta": gf.draw_hyper(rng, -5, -1),
                    "weight_decay": gf.draw_hyper(rng, -7, -3),
                    "max_epochs": MAX_EPOCHS,
                    "seed": SEED,
                }
            )
        rows = []
        with ProcessPoolExecutor(max_workers=search_workers) as pool:
            futures = [pool.submit(gf.search_one, task) for task in tasks]
            for future in as_completed(futures):
                rows.append(future.result())
                pd.DataFrame(rows).sort_values("trial").to_csv(wt_data / "搜索_SearchTrials.csv", index=False)
                log_line(f"{subtype} 搜索进度 {len(rows)}/{N_TRIALS}")
                update_progress(f"{subtype} 搜索 {len(rows)}/{N_TRIALS}")
        trials = pd.DataFrame(rows).sort_values("trial")
        best = trials.sort_values(["select_score", "val_ap"], ascending=False).iloc[0]
        log_line(
            f"{subtype} 选中 trial {int(best['trial'])} lr={best['lr']:.3g} "
            f"beta={best['beta']:.3g} wd={best['weight_decay']:.3g} valAP={best['val_ap']:.4f}"
        )
        cap_mod.prepare("fit", bind_device=True)

        def on_fit_epoch(epoch, ap, best_ap, device, current_lr):
            update_progress(f"{subtype} 训练 {epoch}/{MAX_EPOCHS} valAP {ap:.4f}")
            if epoch == 1 or epoch % 5 == 0 or epoch == MAX_EPOCHS:
                log_line(f"{subtype} 训练 epoch {epoch} valAP {ap:.4f} best {best_ap:.4f}")

        model, fit_metrics = gf.train_until_val_ap_drops(
            data_wt,
            lr=float(best["lr"]),
            beta=float(best["beta"]),
            weight_decay=float(best["weight_decay"]),
            max_epochs=MAX_EPOCHS,
            seed=SEED,
            on_epoch=on_fit_epoch,
        )
        torch.save(model.state_dict(), wt_data / "vgae_state.pt")
        control_name, control_r = choose_control_ahr(selected)
        log_line(f"{subtype} 对照 {control_name} r={control_r:.6f}")
        gene_list = [g for g, _ in present] + [control_name]
        n_response = {}
        for gene in gene_list:
            if gene not in list(selected.var_names):
                log_line(f"{subtype} {gene} 不在网中，跳过")
                continue
            wrapper._target_gene = [gene]
            data_ko = wrapper.load_kodata()
            n_response[gene] = gf.permute_one(model, data_wt, data_ko, subtype, gene, out_root)
            # human enrich already hooked via enrich_response; also run if response exists
            resp = out_root / gene / "数据文件" / "响应基因_Responsive.csv"
            if resp.exists():
                enrich_human(resp, out_root / gene / "数据文件" / "富集_GO.csv", gene)

        text = "\n".join(
            [
                f"subtype={subtype}",
                f"primary={PRIMARY}",
                f"control={control_name}",
                "species=human",
                "response_counts=" + ",".join(f"{g}:{c}" for g, c in n_response.items()),
                f"fit_val_ap={fit_metrics['val_ap']:.6f}",
                f"seconds={time.time() - started:.1f}",
                "formal_done=yes",
            ]
        ) + "\n"
        done_flag.write_text(text, encoding="utf-8")
        (wt_report / "STATUS_GenKI.txt").write_text(text, encoding="utf-8")
        log_line(f"{subtype} GenKI 完成 { (time.time()-started)/60:.1f} min")

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    plan = cap.prepare("grn", bind_device=False)
    (RESULT_DIR / "资源探测_Formal.txt").write_text(cap.format_plan(plan), encoding="utf-8")
    log_line("婷婷 GenKI 开始")
    log_line(cap.format_plan(plan).rstrip())
    try:
        export_mtx()
        run_subtype_ahr(cap, SUBTYPE, int(plan["search"]["trials"]))
    except Exception:
        log_line("中断\n" + traceback.format_exc())
        update_progress("中断，见日志")
        return 1
    update_progress("完成", headline="GenKI 婷婷 AHR 完成")
    log_line("ALL_DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
