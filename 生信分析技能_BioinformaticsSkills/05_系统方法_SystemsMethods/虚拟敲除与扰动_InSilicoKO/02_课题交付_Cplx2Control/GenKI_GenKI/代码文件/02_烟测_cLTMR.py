"""cLTMR GenKI smoke test.

Exercises resource detection, GRN, hyperparameter search, training, and
permutation on the real Control cLTMR matrix. Trial count, epoch cap, and
permutation count are reduced so this run only checks that the path works.
It is not the paper protocol (100 searches, 100 epochs, 1000 permutations).
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import time
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent
DESK = Path(r"C:\Users\10540\Desktop\琪乐无穷\虚拟敲除")
INPUT_DIR = DESK / "结果文件" / "cLTMR" / "GenKI" / "_野生型" / "数据文件"
OUT_DIR = DESK / "结果文件" / "cLTMR" / "GenKI" / "Cplx2" / "数据文件" / "烟测_cLTMR"
TARGET = "Cplx2"
SEED = 8096
N_HVG = 3000
EDGE_PERCENTILE = 85  # keep the top 15% absolute PC-regression weights
SMOKE_TRIALS = 2
SMOKE_EPOCHS = 3
SMOKE_PERMUTATIONS = 3


def load_cap():
    path = CODE_DIR / "00_资源上限_CpuCap.py"
    spec = importlib.util.spec_from_file_location("genki_cpucap", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cpu_name() -> str:
    completed = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "(Get-CimInstance Win32_Processor).Name",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return (completed.stdout or "").strip()


def draw_hyper(rng, exp_low: int, exp_high: int) -> float:
    """Paper grid: coefficient 1-9 times 10^k, k from exp_low through exp_high."""
    exponent = int(rng.integers(exp_low, exp_high + 1))
    coefficient = int(rng.integers(1, 10))
    return float(coefficient) * (10.0 ** exponent)


def train_until_val_ap_drops(data, lr, beta, weight_decay, max_epochs, seed):
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
    best = None
    epochs_run = 0
    for epoch in range(max_epochs):
        model.train()
        optimizer.zero_grad()
        z = model.encode(train_data.x, train_data.edge_index)
        loss = model.recon_loss(
            z,
            train_data.pos_edge_label_index,
            train_data.neg_edge_label_index,
        )
        loss = loss + beta * model.kl_loss()
        loss.backward()
        optimizer.step()
        model.eval()
        with torch.no_grad():
            z_val = model.encode(val_data.x, val_data.edge_index)
            auc, ap = model.test(
                z_val,
                val_data.pos_edge_label_index,
                val_data.neg_edge_label_index,
            )
        epochs_run = epoch + 1
        if best is None or ap > best["val_ap"]:
            best = {
                "epoch": epoch,
                "val_ap": float(ap),
                "val_auc": float(auc),
                "loss": float(loss.detach().cpu()),
                "state": {key: value.detach().cpu().clone() for key, value in model.state_dict().items()},
            }
        else:
            break
    model.load_state_dict(best["state"])
    model.to(device)
    model.eval()
    with torch.no_grad():
        z_test = model.encode(test_data.x, test_data.edge_index)
        test_auc, test_ap = model.test(
            z_test,
            test_data.pos_edge_label_index,
            test_data.neg_edge_label_index,
        )
    best["test_auc"] = float(test_auc)
    best["test_ap"] = float(test_ap)
    best["epochs_run"] = epochs_run
    best["device"] = str(device)
    return model, best


def latent_cpu(model, data):
    import torch

    device = next(model.parameters()).device
    moved = data.to(device)
    model.eval()
    with torch.no_grad():
        model.encode(moved.x, moved.edge_index)
        mu = model.mu.detach().cpu().numpy()
        var = (model.logstd.detach().exp() ** 2).cpu().numpy()
    return mu, var


def main() -> int:
    name = cpu_name()
    if "285K" in name.upper():
        print("Ultra 9 285K is reserved for Knk Formal. GenKI was not started.")
        return 2

    cap = load_cap()
    grn_plan = cap.prepare("grn", bind_device=False)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "资源探测_ResourcePlan.txt").write_text(
        cap.format_plan(grn_plan),
        encoding="utf-8",
    )
    print(cap.format_plan(grn_plan), flush=True)
    print("CPU name:", name, flush=True)

    import numpy as np
    import pandas as pd
    import scipy.io
    import scipy.sparse
    import scanpy as sc
    from sklearn.preprocessing import StandardScaler

    import io

    genes = (INPUT_DIR / "genes.tsv").read_text(encoding="utf-8").splitlines()
    cells = (INPUT_DIR / "cells.tsv").read_text(encoding="utf-8").splitlines()
    mtx_bytes = (INPUT_DIR / "counts.mtx").read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    matrix = scipy.io.mmread(io.BytesIO(mtx_bytes)).T.tocsr()
    if matrix.shape != (len(cells), len(genes)):
        raise SystemExit(f"matrix shape {matrix.shape} != cells x genes {(len(cells), len(genes))}")
    adata = sc.AnnData(matrix)
    adata.obs_names = cells
    adata.var_names = genes
    adata.var_names_make_unique()
    if TARGET not in adata.var_names:
        raise SystemExit("Cplx2 missing from exported counts")

    sc.pp.highly_variable_genes(adata, n_top_genes=N_HVG, flavor="seurat_v3")
    keep = adata.var["highly_variable"].to_numpy().copy()
    forced = False
    target_index = int(np.where(adata.var_names == TARGET)[0][0])
    if not keep[target_index]:
        keep[target_index] = True
        forced = True
    selected = adata[:, keep].copy()
    raw = selected.copy()
    sc.pp.normalize_total(raw, target_sum=1e4)
    sc.pp.log1p(raw)
    selected.layers["norm"] = raw.X.copy()
    dense = raw.X.toarray() if scipy.sparse.issparse(raw.X) else np.asarray(raw.X)
    selected.X = scipy.sparse.csr_matrix(StandardScaler().fit(dense).transform(dense))
    selected.write_h5ad(OUT_DIR / "cLTMR_hvg3000.h5ad")
    print(
        f"HVG {N_HVG} flavor=seurat_v3 cells={selected.n_obs} genes={selected.n_vars} Cplx2_forced={forced}",
        flush=True,
    )

    from GenKI.dataLoader import DataLoader
    from GenKI.train import VGAE_trainer
    from GenKI import utils

    workers = int(grn_plan["grn"]["workers"])
    started = time.time()
    wrapper = DataLoader(
        selected,
        target_gene=[TARGET],
        GRN_file_dir=str(OUT_DIR / "GRNs"),
        rebuild_GRN=True,
        cutoff=EDGE_PERCENTILE,
        n_cpus=workers,
    )
    data_wt = wrapper.load_data()
    data_ko = wrapper.load_kodata()
    grn_seconds = time.time() - started
    print(f"GRN seconds={grn_seconds:.1f} edges={int(data_wt.edge_index.shape[1])}", flush=True)

    search_plan = cap.prepare("search", bind_device=True)
    import torch

    rng = np.random.default_rng(SEED)
    trials = []
    best_trial = None
    best_model = None
    for trial_id in range(SMOKE_TRIALS):
        hyper = {
            "beta": draw_hyper(rng, -5, -1),
            "lr": draw_hyper(rng, -4, -1),
            "weight_decay": draw_hyper(rng, -7, -3),
        }
        model, metrics = train_until_val_ap_drops(
            data_wt,
            lr=hyper["lr"],
            beta=hyper["beta"],
            weight_decay=hyper["weight_decay"],
            max_epochs=SMOKE_EPOCHS,
            seed=SEED,
        )
        row = {"trial": trial_id, **hyper, **{k: v for k, v in metrics.items() if k != "state"}}
        trials.append(row)
        print(
            f"trial {trial_id} lr={hyper['lr']:.3g} beta={hyper['beta']:.3g} "
            f"wd={hyper['weight_decay']:.3g} val_ap={metrics['val_ap']:.4f} device={metrics['device']}",
            flush=True,
        )
        if best_trial is None or metrics["val_ap"] > best_trial["val_ap"]:
            best_trial = row
            best_model = model
    pd.DataFrame(trials).to_csv(OUT_DIR / "搜索_SearchTrials.csv", index=False)

    fit_plan = cap.prepare("fit", bind_device=True)
    model, fit_metrics = train_until_val_ap_drops(
        data_wt,
        lr=best_trial["lr"],
        beta=best_trial["beta"],
        weight_decay=best_trial["weight_decay"],
        max_epochs=SMOKE_EPOCHS,
        seed=SEED,
    )
    best_model = model
    z_mu, z_std = latent_cpu(best_model, data_wt)
    z_mu_ko, z_std_ko = latent_cpu(best_model, data_ko)
    distance = utils.get_distance(z_mu_ko, z_std_ko, z_mu, z_std, by="KL")

    sensei = VGAE_trainer(
        data_wt,
        epochs=SMOKE_EPOCHS,
        lr=best_trial["lr"],
        beta=best_trial["beta"],
        weight_decay=best_trial["weight_decay"],
        seed=SEED,
        verbose=False,
    )
    sensei.model = best_model

    def _safe_latent(self, data, plot_latent_mu=False):
        return latent_cpu(self.model, data)

    sensei.get_latent_vars = _safe_latent.__get__(sensei, VGAE_trainer)
    null = sensei.pmt(data_ko, n=SMOKE_PERMUTATIONS, by="KL")
    ranked = utils.get_generank(data_wt, distance, null, bagging=0.05, cutoff=0.95)
    ranked.to_csv(OUT_DIR / "响应基因_烟测_Responsive.csv")

    genes_out = list(data_wt.y)
    full = pd.DataFrame({"gene": genes_out, "KL": distance})
    full["rank"] = full["KL"].rank(ascending=False, method="min").astype(int)
    full.sort_values(["rank", "gene"], inplace=True)
    full.to_csv(OUT_DIR / "KL排序_烟测_RankKL.csv", index=False)

    import GenKI
    import ray

    versions = "\n".join([
        f"python={sys.version.split()[0]}",
        f"GenKI={getattr(GenKI, '__version__', 'unknown')}",
        f"torch={torch.__version__}",
        f"cuda={torch.cuda.is_available()}",
        f"scanpy={sc.__version__}",
        f"ray={ray.__version__}",
    ])
    status = [
        "run=cLTMR_smoke",
        "claim=计算预测，不是湿实验 KO 差异基因",
        f"cpu={name}",
        cap.format_plan(fit_plan).rstrip(),
        f"seed={SEED}",
        "edge_split_seed=42  # GenKI.preprocessing.split_data hardcodes seed_everything(42)",
        f"hvg=scanpy seurat_v3 n={N_HVG} Cplx2_forced={forced}",
        f"cells={selected.n_obs} genes={selected.n_vars}",
        f"edge_percentile={EDGE_PERCENTILE} (top 15% absolute weights)",
        "nComp=5  # GenKI DataLoader default",
        f"grn_seconds={grn_seconds:.1f} edges={int(data_wt.edge_index.shape[1])}",
        f"smoke_trials={SMOKE_TRIALS} smoke_epochs={SMOKE_EPOCHS} smoke_permutations={SMOKE_PERMUTATIONS}",
        "paper_protocol_not_used=100 trials / 100 epochs / 1000 permutations",
        f"chosen_lr={best_trial['lr']}",
        f"chosen_beta={best_trial['beta']}",
        f"chosen_weight_decay={best_trial['weight_decay']}",
        f"fit_val_auc={fit_metrics['val_auc']:.6f}",
        f"fit_val_ap={fit_metrics['val_ap']:.6f}",
        f"fit_test_auc={fit_metrics['test_auc']:.6f}",
        f"fit_test_ap={fit_metrics['test_ap']:.6f}",
        f"fit_best_epoch={fit_metrics['epoch']}",
        f"fit_epochs_run={fit_metrics['epochs_run']}",
        f"fit_device={fit_metrics['device']}",
        f"responsive_rows={0 if ranked is None else len(ranked)}",
        "responsive_rule=KL top 5% and hit >= 95% of permutations (GenKI get_generank defaults)",
        "permutation=GenKI.pmt bootstrap of cell columns, seed 0 inside pmt",
        versions.rstrip(),
        f"torch_cuda_device={torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'}",
    ]
    (OUT_DIR / "STATUS_烟测_cLTMR.txt").write_text("\n".join(status) + "\n", encoding="utf-8")
    print("SMOKE_DONE", OUT_DIR, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
