"""Formal GenKI run for the current Control TG subtypes (PEP, NF1).

Paper protocol: 100 random searches, at most 100 epochs with early stop on
validation AP, then 1000 no-replacement cell-order permutations (numpy
permutation, seed 0). Search workers call prepare("search") before importing
NumPy or PyTorch.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
import traceback
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent
DESKTOP = Path(r"C:\Users\10540\Desktop\琪乐无穷\虚拟敲除")
RESULT_DIR = DESKTOP / "结果文件" / "_跨亚群" / "GenKI" / "报告文件"
RUN_ID = "pep_nf1"
PROGRESS_JSON = RESULT_DIR / f"进度_状态_{RUN_ID}.json"
PROGRESS_TXT = RESULT_DIR / f"进度_Progress_{RUN_ID}.txt"
RUN_LOG = RESULT_DIR / f"正式运行日志_{RUN_ID}.log"
RSCRIPT = Path(r"E:\R-4.6.0\bin\Rscript.exe")
EXPORT_R = CODE_DIR / "01_导出亚群计数_ExportSubtype.R"
ENRICH_R = CODE_DIR / "04_焦点通路_EnrichResponse.R"
KEGG_R = CODE_DIR / "08_KEGG富集_EnrichKEGG.R"

TARGET = "Cplx2"
SEED = 8096
N_HVG = 3000
EDGE_PERCENTILE = 85
N_TRIALS = 100
MAX_EPOCHS = 100
MIN_EPOCHS = 10
EARLY_STOP_PATIENCE = 15
EARLY_STOP_MIN_DELTA = 1e-4
LR_PLATEAU_PATIENCE = 5
LR_PLATEAU_FACTOR = 0.5
N_PERMUTATIONS = 1000
SUBTYPES = ("PEP", "NF1")
KNOCK_GENES = ("Mitf", "Bace2", "Cplx2", "Ppp1r26", "Slc28a3", "Sh3d21")


def load_cap():
    path = CODE_DIR / "00_资源上限_CpuCap.py"
    spec = importlib.util.spec_from_file_location("genki_cpucap", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cpu_name() -> str:
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"],
        capture_output=True,
        text=True,
        check=False,
    )
    return (completed.stdout or "").strip()


def _lock():
    from filelock import FileLock

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    return FileLock(str(RESULT_DIR / "进度.lock"))


def log_line(message: str) -> None:
    stamp = time.strftime("%H:%M:%S")
    line = f"{stamp}  {message}\n"
    with _lock():
        with RUN_LOG.open("a", encoding="utf-8") as handle:
            handle.write(line)
    print(line, end="", flush=True)


def update_progress(key: str, text: str, headline: str | None = None) -> None:
    with _lock():
        state = {"headline": "", "slots": {}}
        if PROGRESS_JSON.exists():
            state.update(json.loads(PROGRESS_JSON.read_text(encoding="utf-8")))
        if headline is not None:
            state["headline"] = headline
        state["slots"][key] = text
        PROGRESS_JSON.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        lines = [state.get("headline") or "GenKI 正式运行", ""]
        for slot in sorted(state["slots"]):
            lines.append(f"{slot}  {state['slots'][slot]}")
        lines.append("")
        lines.append("完整日志: " + str(RUN_LOG))
        PROGRESS_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def draw_hyper(rng, exp_low: int, exp_high: int) -> float:
    exponent = int(rng.integers(exp_low, exp_high + 1))
    coefficient = int(rng.integers(1, 10))
    return float(coefficient) * (10.0 ** exponent)


def train_until_val_ap_drops(data, lr, beta, weight_decay, max_epochs, seed, on_epoch=None):
    import torch
    from GenKI.model import VGAE
    from GenKI.preprocessing import split_data
    from GenKI.train import VariationalGCNEncoder

    train_data, val_data, test_data = split_data(data=data)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    model = VGAE(VariationalGCNEncoder(data.num_features, 2))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    train_data = train_data.to(device)
    val_data = val_data.to(device)
    test_data = test_data.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=LR_PLATEAU_FACTOR,
        patience=LR_PLATEAU_PATIENCE,
        threshold=EARLY_STOP_MIN_DELTA,
        threshold_mode="abs",
        min_lr=lr / 100.0,
    )
    best = None
    epochs_run = 0
    stale = 0
    for epoch in range(max_epochs):
        model.train()
        optimizer.zero_grad()
        latent = model.encode(train_data.x, train_data.edge_index)
        loss = model.recon_loss(
            latent,
            train_data.pos_edge_label_index,
            train_data.neg_edge_label_index,
        )
        loss = loss + beta * model.kl_loss()
        loss.backward()
        optimizer.step()
        model.eval()
        with torch.no_grad():
            latent_val = model.encode(val_data.x, val_data.edge_index)
            auc, ap = model.test(
                latent_val,
                val_data.pos_edge_label_index,
                val_data.neg_edge_label_index,
            )
        epochs_run = epoch + 1
        current_lr = float(optimizer.param_groups[0]["lr"])
        improved = best is None or ap > best["val_ap"] + EARLY_STOP_MIN_DELTA
        if improved:
            best = {
                "epoch": epoch,
                "val_ap": float(ap),
                "val_auc": float(auc),
                "loss": float(loss.detach().cpu()),
                "lr_at_best": current_lr,
                "state": {key: value.detach().cpu().clone() for key, value in model.state_dict().items()},
            }
            stale = 0
        else:
            stale += 1
        scheduler.step(float(ap))
        if on_epoch is not None:
            on_epoch(epochs_run, float(ap), best["val_ap"], str(device), current_lr)
        if epochs_run >= MIN_EPOCHS and stale >= EARLY_STOP_PATIENCE:
            break
    model.load_state_dict(best["state"])
    model.to(device)
    model.eval()
    with torch.no_grad():
        latent_train = model.encode(train_data.x, train_data.edge_index)
        train_auc, train_ap = model.test(
            latent_train,
            train_data.pos_edge_label_index,
            train_data.neg_edge_label_index,
        )
        latent_test = model.encode(test_data.x, test_data.edge_index)
        test_auc, test_ap = model.test(
            latent_test,
            test_data.pos_edge_label_index,
            test_data.neg_edge_label_index,
        )
    best["train_auc"] = float(train_auc)
    best["train_ap"] = float(train_ap)
    best["gap"] = float(train_ap) - best["val_ap"]
    best["select_score"] = best["val_ap"] - max(0.0, best["gap"])
    best["test_auc"] = float(test_auc)
    best["test_ap"] = float(test_ap)
    best["epochs_run"] = epochs_run
    best["device"] = str(device)
    best["lr_end"] = float(optimizer.param_groups[0]["lr"])
    return model, best


def search_one(task: dict) -> dict:
    """One hyperparameter trial. Runs in its own process."""
    cap = load_cap()
    cap.prepare("search", bind_device=True)
    import numpy as np
    import torch
    from torch_geometric.data import Data

    graph_path = Path(task["graph_npz"])
    with np.load(graph_path) as stored:
        features = stored["x"]
        edges = stored["edge_index"]
    genes = (graph_path.with_name("genes.txt")).read_text(encoding="utf-8").splitlines()
    data = Data(
        x=torch.tensor(features, dtype=torch.float),
        edge_index=torch.tensor(edges, dtype=torch.long),
        y=genes,
    )
    subtype = task["subtype"]
    trial = int(task["trial"])
    total = int(task["n_trials"])
    key = f"{subtype} 搜索 {trial + 1}/{total}"
    update_progress(key, "已启动，等待第 1 轮")
    log_line(f"{key} 开始 lr={task['lr']:.3g} beta={task['beta']:.3g} wd={task['weight_decay']:.3g}")

    def on_epoch(epoch, ap, best_ap, device, current_lr):
        update_progress(
            key,
            f"第 {epoch}/{task['max_epochs']} 轮  本轮验证AP {ap:.4f}  目前最好 {best_ap:.4f}  lr {current_lr:.3g}  {device}",
        )
        if epoch == 1 or epoch % 5 == 0 or epoch == task["max_epochs"]:
            log_line(
                f"{key}  第 {epoch}/{task['max_epochs']} 轮  验证AP {ap:.4f}  最好 {best_ap:.4f}  lr {current_lr:.3g}"
            )

    started = time.time()
    _model, metrics = train_until_val_ap_drops(
        data,
        lr=float(task["lr"]),
        beta=float(task["beta"]),
        weight_decay=float(task["weight_decay"]),
        max_epochs=int(task["max_epochs"]),
        seed=int(task["seed"]),
        on_epoch=on_epoch,
    )
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    row = {
        "trial": trial,
        "lr": float(task["lr"]),
        "beta": float(task["beta"]),
        "weight_decay": float(task["weight_decay"]),
        "seconds": round(time.time() - started, 1),
    }
    row.update({item: value for item, value in metrics.items() if item != "state"})
    update_progress(key, f"完成  验证AP {row['val_ap']:.4f}  用了 {row['epochs_run']} 轮  {row['seconds']}s")
    log_line(
        f"{key} 完成 验证AP {row['val_ap']:.4f} 训练AP {row['train_ap']:.4f} "
        f"差距 {row['gap']:.4f} 挑选分 {row['select_score']:.4f} "
        f"轮数 {row['epochs_run']} 用时 {row['seconds']}s"
    )
    return row


def latent_cpu(model, data):
    import torch

    device = next(model.parameters()).device
    moved = data.to(device)
    model.eval()
    with torch.no_grad():
        model.encode(moved.x, moved.edge_index)
        mu = model.mu.detach().cpu().numpy()
        variance = (model.logstd.detach().exp() ** 2).cpu().numpy()
    return mu, variance


def read_counts(subtype: str):
    import io

    import scipy.io

    folder = DESKTOP / "结果文件" / subtype / "GenKI" / "_野生型" / "数据文件"
    genes = (folder / "genes.tsv").read_text(encoding="utf-8").splitlines()
    cells = (folder / "cells.tsv").read_text(encoding="utf-8").splitlines()
    raw = (folder / "counts.mtx").read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    matrix = scipy.io.mmread(io.BytesIO(raw)).T.tocsr()
    if matrix.shape != (len(cells), len(genes)):
        raise RuntimeError(f"{subtype} matrix {matrix.shape} != {(len(cells), len(genes))}")
    return matrix, genes, cells


def prepare_adata(subtype: str, force_genes: list[str]):
    import numpy as np
    import scipy.sparse
    import scanpy as sc
    from sklearn.preprocessing import StandardScaler

    matrix, genes, cells = read_counts(subtype)
    adata = sc.AnnData(matrix)
    adata.obs_names = cells
    adata.var_names = genes
    adata.var_names_make_unique()
    sc.pp.highly_variable_genes(adata, n_top_genes=N_HVG, flavor="seurat_v3")
    keep = adata.var["highly_variable"].to_numpy().copy()
    forced = []
    for gene in force_genes:
        if gene not in adata.var_names:
            continue
        index = int(np.where(adata.var_names == gene)[0][0])
        if not keep[index]:
            keep[index] = True
            forced.append(gene)
    selected = adata[:, keep].copy()
    raw = selected.copy()
    sc.pp.normalize_total(raw, target_sum=1e4)
    sc.pp.log1p(raw)
    selected.layers["norm"] = raw.X.copy()
    dense = raw.X.toarray() if scipy.sparse.issparse(raw.X) else np.asarray(raw.X)
    selected.X = scipy.sparse.csr_matrix(StandardScaler().fit(dense).transform(dense))
    return selected, forced


def response_table(genes, distance, null):
    import numpy as np
    import pandas as pd

    order = np.argsort(null, axis=1)
    threshold = int(len(genes) * 0.95)
    top = order[:, threshold:].reshape(-1)
    hits = np.bincount(top, minlength=len(genes))
    minimum = int(null.shape[0] * 0.95)
    frame = pd.DataFrame({"gene": list(genes), "KL": distance, "hit": hits})
    frame["hit_fraction"] = frame["hit"] / float(null.shape[0])
    frame["rank"] = frame["KL"].rank(ascending=False, method="min").astype(int)
    passed = frame[(frame["hit"] > minimum) & (frame["KL"] != 0)].copy()
    passed.sort_values(["KL", "hit"], ascending=[False, False], inplace=True)
    frame.sort_values(["rank", "gene"], inplace=True)
    return frame, passed, minimum


def enrich_response(gene_csv: Path, out_csv: Path, knockout: str = "") -> str:
    if not ENRICH_R.exists():
        return "enrichment script missing"
    cmd = [str(RSCRIPT), str(ENRICH_R), str(gene_csv), str(out_csv)]
    if knockout:
        cmd.append(knockout)
    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    message = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0:
        return "enrichment failed: " + message[-500:]
    return message.strip().splitlines()[-1] if message.strip() else "enrichment wrote " + out_csv.name


def run_kegg_batch() -> str:
    """Run mouse KEGG ORA for every GenKI gene that already has a response table."""
    if not KEGG_R.exists():
        return "KEGG script missing"
    completed = subprocess.run(
        [str(RSCRIPT), str(KEGG_R)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    message = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0:
        return "KEGG failed: " + message[-800:]
    return message.strip().splitlines()[-1] if message.strip() else "KEGG_DONE"


def detected_knock_genes(subtype: str) -> list[tuple[str, int]]:
    matrix, genes, _cells = read_counts(subtype)
    names = list(genes)
    kept = []
    for gene in KNOCK_GENES:
        if gene not in names:
            log_line(f"{subtype} {gene} 不在矩阵中，不敲")
            continue
        detected = int((matrix[:, names.index(gene)] > 0).sum())
        if detected == 0:
            log_line(f"{subtype} {gene} 检出细胞数为 0，不敲")
            continue
        kept.append((gene, detected))
        log_line(f"{subtype} {gene} 检出细胞 {detected}")
    return kept


def choose_control(selected) -> tuple[str, float]:
    import numpy as np

    matrix = selected.layers["norm"]
    if hasattr(matrix, "toarray"):
        matrix = matrix.toarray()
    names = list(selected.var_names)
    cplx = matrix[:, names.index("Cplx2")]
    banned = set(KNOCK_GENES)
    best_name = None
    best_r = None
    for index, name in enumerate(names):
        if name in banned or float(np.std(matrix[:, index])) == 0.0:
            continue
        corr = float(np.corrcoef(matrix[:, index], cplx)[0, 1])
        if np.isnan(corr):
            continue
        if best_r is None or abs(corr) < abs(best_r):
            best_name = name
            best_r = corr
    if best_name is None:
        raise RuntimeError("no control gene")
    return best_name, best_r


def permute_one(model, data_wt, data_ko, subtype: str, gene: str, out_dir: Path) -> int:
    import numpy as np
    import torch
    from torch_geometric.data import Data
    from GenKI import utils

    genes = list(map(str, data_wt.y))
    z_mu, z_std = latent_cpu(model, data_wt)
    z_mu_ko, z_std_ko = latent_cpu(model, data_ko)
    distance = utils.get_distance(z_mu_ko, z_std_ko, z_mu, z_std, by="KL")
    n_cell = int(data_wt.x.shape[1])
    np.random.seed(0)
    null_rows = []
    started = time.time()
    for index in range(N_PERMUTATIONS):
        chosen = np.random.permutation(n_cell)
        wild = Data(x=data_wt.x[:, chosen].clone(), edge_index=data_wt.edge_index, y=genes)
        knocked = Data(x=data_ko.x[:, chosen].clone(), edge_index=data_ko.edge_index, y=genes)
        mu_w, var_w = latent_cpu(model, wild)
        mu_k, var_k = latent_cpu(model, knocked)
        null_rows.append(utils.get_distance(mu_k, var_k, mu_w, var_w, by="KL"))
        done = index + 1
        if done == 1 or done % 100 == 0 or done == N_PERMUTATIONS:
            update_progress("当前阶段", f"{subtype} {gene} 排列 {done}/{N_PERMUTATIONS}")
            log_line(f"{subtype} {gene} 排列 {done}/{N_PERMUTATIONS}  已用 {time.time() - started:.0f}s")
    full, passed, _minimum = response_table(genes, distance, np.vstack(null_rows))
    gene_dir = out_dir / gene / "数据文件"
    note_dir = out_dir / gene / "报告文件"
    gene_dir.mkdir(parents=True, exist_ok=True)
    note_dir.mkdir(parents=True, exist_ok=True)
    full.to_csv(gene_dir / "KL排序_RankKL.csv", index=False)
    passed.to_csv(gene_dir / "响应基因_Responsive.csv", index=False)
    if len(passed) > 0:
        note = enrich_response(
            gene_dir / "响应基因_Responsive.csv",
            gene_dir / "富集_GO.csv",
            gene,
        )
        stray_note = gene_dir / "焦点通路_EnrichNote.txt"
        if stray_note.exists():
            stray_note.replace(note_dir / "焦点通路_EnrichNote.txt")
        log_line(f"{subtype} {gene} GO富集 {note}")
        # KEGG is batch-scripted over the result tree (same BH p/q); run per gene via shared script args path is whole-tree.
    else:
        write_empty = note_dir / "05_富集_无通过条目.txt"
        write_empty.write_text(
            "GenKI 响应基因（KL top5% 且 >95% 重复出现）为 0，不做富集。\n",
            encoding="utf-8",
        )
        log_line(f"{subtype} {gene} 没有响应基因，不做富集")
    del torch
    return len(passed)


def run_subtype(cap, subtype: str, search_workers: int, out_dir=None) -> None:
    import numpy as np
    import pandas as pd
    import torch
    from concurrent.futures import ProcessPoolExecutor, as_completed
    from GenKI.dataLoader import DataLoader
    from GenKI import utils

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
    update_progress("当前阶段", f"{subtype} 建网", headline=f"正式运行 {RUN_ID} {subtype}")
    log_line(f"{subtype} 开始建网")

    present = detected_knock_genes(subtype)
    if not any(gene == "Cplx2" for gene, _count in present):
        log_line(f"{subtype} 没有 Cplx2，跳过")
        return
    selected, forced = prepare_adata(subtype, [gene for gene, _count in present])
    selected.write_h5ad(wt_data / f"{subtype}_hvg3000.h5ad")
    log_line(
        f"{subtype} HVG cells={selected.n_obs} genes={selected.n_vars} forced={','.join(forced) or 'none'}"
    )
    grn_started = time.time()
    wrapper = DataLoader(
        selected,
        target_gene=["Cplx2"],
        GRN_file_dir=str(wt_data / "GRNs"),
        rebuild_GRN=True,
        cutoff=EDGE_PERCENTILE,
        n_cpus=int(cap.prepare("grn", bind_device=False)["grn"]["workers"]),
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
    log_line(
        f"{subtype} 建网完成 {time.time() - grn_started:.1f}s 边 {int(data_wt.edge_index.shape[1])}"
    )

    rng = np.random.default_rng(SEED)
    tasks = []
    for trial in range(N_TRIALS):
        tasks.append(
            {
                "trial": trial,
                "subtype": subtype,
                "n_trials": N_TRIALS,
                "graph_npz": str(graph_path),
                "lr": draw_hyper(rng, -4, -1),
                "beta": draw_hyper(rng, -5, -1),
                "weight_decay": draw_hyper(rng, -7, -3),
                "max_epochs": MAX_EPOCHS,
                "seed": SEED,
            }
        )
    update_progress("当前阶段", f"{subtype} 搜索 0/{N_TRIALS}", headline=f"正式运行 {RUN_ID} {subtype}")
    rows = []
    with ProcessPoolExecutor(max_workers=search_workers) as pool:
        futures = [pool.submit(search_one, task) for task in tasks]
        for future in as_completed(futures):
            rows.append(future.result())
            pd.DataFrame(rows).sort_values("trial").to_csv(wt_data / "搜索_SearchTrials.csv", index=False)
            log_line(f"{subtype} 搜索进度 {len(rows)}/{N_TRIALS}")
    trials = pd.DataFrame(rows).sort_values("trial")
    trials.to_csv(wt_data / "搜索_SearchTrials.csv", index=False)
    best = trials.sort_values(["select_score", "val_ap"], ascending=False).iloc[0]
    log_line(
        f"{subtype} 搜索选中 trial {int(best['trial'])} lr={best['lr']:.3g} "
        f"beta={best['beta']:.3g} wd={best['weight_decay']:.3g} "
        f"验证AP {best['val_ap']:.4f} 训练AP {best['train_ap']:.4f} 差距 {best['gap']:.4f}"
    )

    cap.prepare("fit", bind_device=True)
    update_progress("当前阶段", f"{subtype} 正式训练", headline=f"正式运行 {RUN_ID} {subtype}")

    def on_fit_epoch(epoch, ap, best_ap, device, current_lr):
        update_progress(
            "当前阶段",
            f"{subtype} 正式训练 第 {epoch}/{MAX_EPOCHS} 轮 验证AP {ap:.4f} lr {current_lr:.3g}",
        )
        if epoch == 1 or epoch % 5 == 0 or epoch == MAX_EPOCHS:
            log_line(
                f"{subtype} 正式训练 第 {epoch}/{MAX_EPOCHS} 轮 验证AP {ap:.4f} 最好 {best_ap:.4f} lr {current_lr:.3g}"
            )

    model, fit_metrics = train_until_val_ap_drops(
        data_wt,
        lr=float(best["lr"]),
        beta=float(best["beta"]),
        weight_decay=float(best["weight_decay"]),
        max_epochs=MAX_EPOCHS,
        seed=SEED,
        on_epoch=on_fit_epoch,
    )
    torch.save(model.state_dict(), wt_data / "vgae_state.pt")
    control_name, control_r = choose_control(selected)
    log_line(f"{subtype} 对照基因 {control_name} r={control_r:.6f}")
    gene_list = [gene for gene, _count in present] + [control_name]
    n_response = {}
    for gene in gene_list:
        if gene not in list(selected.var_names):
            log_line(f"{subtype} {gene} 不在 3000 基因网中，不敲")
            continue
        wrapper._target_gene = [gene]
        data_ko = wrapper.load_kodata()
        n_response[gene] = permute_one(model, data_wt, data_ko, subtype, gene, out_root)

    elapsed = time.time() - started
    status = [
        f"subtype={subtype}",
        f"run=formal_{RUN_ID}",
        "early_stop=min_epochs 10; patience 15; min_delta 1e-4; restore best val AP",
        "lr_schedule=ReduceLROnPlateau factor 0.5 patience 5 min_lr=initial/100",
        "selection=val_ap - max(0, train_ap - val_ap)",
        "claim=计算预测，不是湿实验 KO 差异基因",
        "dataset=GSE197289 Control; not a chronic trigeminal neuralgia model",
        f"cells={selected.n_obs}",
        f"genes={selected.n_vars}",
        f"forced={','.join(forced) or 'none'}",
        f"knock_genes={','.join(gene for gene, _count in present)}",
        f"control_gene={control_name}",
        f"control_pearson_r={control_r:.6f}",
        f"edge_percentile={EDGE_PERCENTILE}",
        f"edges={int(data_wt.edge_index.shape[1])}",
        "latent_dim=2",
        f"trials={N_TRIALS}",
        f"max_epochs={MAX_EPOCHS}",
        f"permutations={N_PERMUTATIONS}",
        f"seed={SEED}",
        "edge_split_seed=42",
        f"chosen_trial={int(best['trial'])}",
        f"chosen_lr={best['lr']:.8g}",
        f"chosen_beta={best['beta']:.8g}",
        f"chosen_weight_decay={best['weight_decay']:.8g}",
        f"fit_train_ap={fit_metrics['train_ap']:.6f}",
        f"fit_gap={fit_metrics['gap']:.6f}",
        f"fit_select_score={fit_metrics['select_score']:.6f}",
        f"fit_val_auc={fit_metrics['val_auc']:.6f}",
        f"fit_val_ap={fit_metrics['val_ap']:.6f}",
        f"fit_lr_at_best={fit_metrics['lr_at_best']:.8g}",
        f"fit_lr_end={fit_metrics['lr_end']:.8g}",
        f"fit_test_auc={fit_metrics['test_auc']:.6f}",
        f"fit_test_ap={fit_metrics['test_ap']:.6f}",
        f"fit_best_epoch={fit_metrics['epoch']}",
        f"fit_epochs_run={fit_metrics['epochs_run']}",
        f"fit_device={fit_metrics['device']}",
        "response_rule=KL in top 5% of a replicate and hit > 95% of 1000 replicates",
        "permutation=shuffle cell columns without replacement, numpy seed 0",
        "response_counts=" + ",".join(f"{gene}:{count}" for gene, count in n_response.items()),
        f"seconds={elapsed:.1f}",
        "formal_done=yes",
    ]
    text = "\n".join(status) + "\n"
    (wt_report / "STATUS_GenKI.txt").write_text(text, encoding="utf-8")
    with (RESULT_DIR / f"STATUS_GenKI_{RUN_ID}.txt").open("a", encoding="utf-8") as handle:
        handle.write("\n" + text)
    done_flag.write_text(text, encoding="utf-8")
    log_line(f"{subtype} 正式完成 用时 {elapsed / 60:.1f} 分钟")


def export_all() -> None:
    log_line("导出亚群计数，已有的会跳过")
    for subtype in SUBTYPES:
        completed = subprocess.run(
            [str(RSCRIPT), str(EXPORT_R), subtype],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(subtype + ": " + (completed.stderr[-2000:] or completed.stdout[-2000:]))
        log_line(f"{subtype} 导出结束")


def main() -> int:
    name = cpu_name()
    # Knk Formal on this machine finished 2026-10-03 12:18; resource probe governs now.
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    cap = load_cap()
    plan = cap.prepare("grn", bind_device=False)
    (RESULT_DIR / "资源探测_Formal.txt").write_text(cap.format_plan(plan), encoding="utf-8")
    log_line("正式运行开始")
    log_line(cap.format_plan(plan).rstrip())
    log_line("CPU " + name)
    export_all()
    search_workers = int(plan["search"]["trials"])
    try:
        for subtype in SUBTYPES:
            run_subtype(cap, subtype, search_workers)
    except Exception:
        log_line("正式运行中断\n" + traceback.format_exc())
        update_progress("当前阶段", "中断，见正式运行日志")
        return 1
    kegg_note = run_kegg_batch()
    log_line("KEGG 批处理 " + kegg_note)
    update_progress("当前阶段", "PEP NF1 已完成（含 GO/KEGG）", headline="正式运行完成")
    log_line("PEP NF1 正式运行完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
