"""Compare one small leave-one-out SVD on CPU and GPU.

GPU stays off unless it is both faster and within 1e-5 of the CPU coefficients.
One CPU thread. Does not load Formal counts.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

import numpy as np

from knk_accel.pcnet import limit_threads, truncated_coefficients


def _gpu_coefficients(x_std: np.ndarray, n_comp: int = 3):
    import torch

    torch.set_num_threads(1)
    if not torch.cuda.is_available():
        return None
    device = torch.device("cuda")
    xt = torch.as_tensor(x_std, dtype=torch.float64, device=device)
    n_genes = xt.shape[1]
    out = torch.empty((n_genes, n_genes - 1), dtype=torch.float64, device=device)
    for gene_index in range(n_genes):
        target = xt[:, gene_index]
        design = torch.cat((xt[:, :gene_index], xt[:, gene_index + 1 :]), dim=1)
        _u, _s, vh = torch.linalg.svd(design, full_matrices=False)
        components = vh[:n_comp].T
        scores = design @ components
        norms = torch.sum(scores * scores, dim=0)
        scores = scores / norms
        out[gene_index] = components @ (scores.T @ target)
    return out.detach().cpu().numpy()


def main() -> None:
    limit_threads()
    rng = np.random.default_rng(3)
    raw = rng.normal(size=(40, 20))
    centered = raw - raw.mean(axis=0, keepdims=True)
    scale = centered.std(axis=0, ddof=1, keepdims=True)
    x_std = centered / scale
    t0 = time.perf_counter()
    cpu = truncated_coefficients(x_std, n_comp=3)
    cpu_s = time.perf_counter() - t0
    decision = "GPU 不启用。"
    gpu_s = None
    diff = None
    try:
        t1 = time.perf_counter()
        gpu = _gpu_coefficients(x_std, n_comp=3)
        gpu_s = time.perf_counter() - t1
        if gpu is None:
            decision = "GPU 不启用。CUDA 不可用。"
        else:
            diff = float(np.max(np.abs(cpu - gpu)))
            if diff < 1e-5 and gpu_s < cpu_s:
                decision = "小矩阵上 GPU 又快又对齐，但仍不接入正在跑的 Formal。"
            elif diff >= 1e-5:
                decision = "GPU 不启用。系数和 CPU 截断 SVD 对不上。"
            else:
                decision = "GPU 不启用。这次小矩阵上 GPU 不比 CPU 快。"
    except Exception as exc:
        decision = f"GPU 不启用。运行失败：{type(exc).__name__}: {exc}"

    docs = CODE_DIR.parent / "文档_docs"
    docs.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GPU 门槛",
        "",
        "矩阵：40 样本 × 20 基因，nComp=3，CPU 线程 1。GPU 这边用的是完整 SVD 再留 3 个分量，用来看小矩阵值不值得搬上显卡。",
        "",
        f"- CPU 截断 SVD：{cpu_s:.3f} 秒",
        f"- GPU：{gpu_s:.3f} 秒" if gpu_s is not None else "- GPU：未完成",
        f"- 最大绝对差：{diff:.3e}" if diff is not None else "- 最大绝对差：无",
        f"- 决定：{decision}",
        "",
        "这种尺寸盖不住内核启动开销，不能代表 400×8000。Formal 不迁到 GPU。",
        "",
    ]
    text = "\n".join(lines)
    (docs / "GPU门槛_GpuGate.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
