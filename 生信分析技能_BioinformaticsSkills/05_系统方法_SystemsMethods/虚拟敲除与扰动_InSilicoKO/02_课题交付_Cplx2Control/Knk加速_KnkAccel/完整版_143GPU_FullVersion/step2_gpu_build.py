"""步骤 2：1.4.3 GPU 建网 + 稀疏 CP 分解。

并发数来自探测（plan.net_workers），线程/设备不写死。
GPU 并发时每个 worker 用自己的 CUDA stream，数值与串行一致。
"""

from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import config_配置 as config  # noqa: E402
import probe_资源探测 as probe_mod  # noqa: E402
from knk_accel.cp_decomp import tensor_from_networks_gpu  # noqa: E402
from knk_accel.versions import pcnet_143  # noqa: E402

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

ALGO = "scTenifoldKnk_1.4.3_GPU"


def load_cpm(folder: Path):
    genes = (folder / "genes.txt").read_text(encoding="utf-8").splitlines()
    raw = np.fromfile(folder / "cpm.bin", dtype=np.float64)
    return raw.reshape((len(genes), raw.size // len(genes)), order="F"), genes


def load_indices(folder: Path, net_id: int) -> np.ndarray:
    text = (folder / f"net_{net_id:02d}_indices.txt").read_text(encoding="utf-8").split()
    return np.asarray([int(item) for item in text], dtype=np.int64)


def write_csr(path: Path, matrix: np.ndarray) -> None:
    csr = sparse.csr_matrix(matrix)
    with path.open("wb") as handle:
        np.asarray([csr.shape[0], csr.shape[1], csr.nnz], dtype=np.int32).tofile(handle)
        np.asarray(csr.indptr, dtype=np.int32).tofile(handle)
        np.asarray(csr.indices, dtype=np.int32).tofile(handle)
        np.asarray(csr.data, dtype=np.float64).tofile(handle)


def read_csr(path: Path) -> sparse.csr_matrix:
    with path.open("rb") as handle:
        nrow, ncol, nnz = np.fromfile(handle, dtype=np.int32, count=3)
        indptr = np.fromfile(handle, dtype=np.int32, count=int(nrow) + 1)
        indices = np.fromfile(handle, dtype=np.int32, count=int(nnz))
        data = np.fromfile(handle, dtype=np.float64, count=int(nnz))
    return sparse.csr_matrix((data, indices, indptr), shape=(int(nrow), int(ncol)))


def r_init(folder: Path, n_gene: int, rscript: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    import subprocess

    script = folder / "_init.R"
    script.write_text(
        "\n".join(
            [
                "args <- commandArgs(trailingOnly=TRUE)",
                "out <- args[[1]]; n <- as.integer(args[[2]])",
                f"set.seed({config.SEED})",
                "writeBin(as.numeric(matrix(rnorm(n*3), n, 3)), file(file.path(out,'u1.bin'),'wb'))",
                "writeBin(as.numeric(matrix(rnorm(n*3), n, 3)), file(file.path(out,'u2.bin'),'wb'))",
                "writeBin(as.numeric(matrix(rnorm(10*3), 10, 3)), file(file.path(out,'u3.bin'),'wb'))",
            ]
        ),
        encoding="utf-8",
    )
    subprocess.run([rscript, "--vanilla", str(script), str(folder), str(n_gene)], check=True)
    u1 = np.fromfile(folder / "u1.bin", dtype=np.float64).reshape((n_gene, 3), order="F")
    u2 = np.fromfile(folder / "u2.bin", dtype=np.float64).reshape((n_gene, 3), order="F")
    u3 = np.fromfile(folder / "u3.bin", dtype=np.float64).reshape((10, 3), order="F")
    return u1, u2, u3


def build_one(counts: np.ndarray, genes_n: int, folder: Path, net_id: int, use_gpu: bool) -> float:
    path = folder / f"gpu_net_{net_id:02d}.csr"
    if path.exists() and path.stat().st_size > 1000:
        print("skip net", net_id, flush=True)
        return 0.0
    started = time.perf_counter()
    if use_gpu:
        import torch

        stream = torch.cuda.Stream()
        with torch.cuda.stream(stream):
            network = pcnet_143(counts[:, load_indices(folder, net_id)], n_comp=config.N_COMP, q=config.Q, device="gpu")
        stream.synchronize()
    else:
        network = pcnet_143(counts[:, load_indices(folder, net_id)], n_comp=config.N_COMP, q=config.Q, device="cpu")
    elapsed = time.perf_counter() - started
    write_csr(path, np.asarray(network))
    print("net", net_id, f"{elapsed:.3f}s", flush=True)
    del network
    return elapsed


def one_subtype(subtype: str, plan: dict) -> None:
    folder = config.RESULT_DIR / subtype / ALGO / "_野生型" / "数据文件"
    note = config.RESULT_DIR / subtype / ALGO / "_野生型" / "报告文件"
    note.mkdir(parents=True, exist_ok=True)
    counts, genes = load_cpm(folder)
    use_gpu = bool(plan["cuda"])
    workers = int(plan["net_workers"])
    print(subtype, "genes", len(genes), "workers", workers, "device", "gpu" if use_gpu else "cpu", flush=True)

    lines = ["net,seconds,genes,workers"]
    ids = list(range(1, config.N_NET + 1))
    if workers > 1 and use_gpu:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(lambda i: build_one(counts, len(genes), folder, i, use_gpu), ids))
    elif workers > 1:
        from concurrent.futures import ProcessPoolExecutor

        with ProcessPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(_build_one_cpu, [(str(folder), i, config.N_COMP, config.Q) for i in ids]))
    else:
        results = [build_one(counts, len(genes), folder, i, use_gpu) for i in ids]
    for net_id, elapsed in zip(ids, results):
        lines.append(f"{net_id},{elapsed:.3f},{len(genes)},{workers}")
    (note / "gpu_network_times.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    if (folder / "gpu_wt_rounded.bin").exists() and (folder / "genes.txt").exists():
        print(subtype, "gpu_wt_rounded.bin exists, skip tensor", flush=True)
        return
    nets = [read_csr(folder / f"gpu_net_{i:02d}.csr") for i in ids]
    init = r_init(folder, len(genes), plan["rscript"])
    started = time.perf_counter()
    result = tensor_from_networks_gpu(
        nets, init, n_comp=config.N_COMP, max_iter=1000, tol=1e-5, n_decimal=config.N_DECIMAL
    )
    elapsed = time.perf_counter() - started
    matrix = np.asarray(result["matrix"])
    matrix.tofile(folder / "gpu_wt_rounded.bin")
    (note / "gpu_tensor.txt").write_text(
        f"seconds={elapsed:.3f}\niterations={result['iterations']}\nconverged={result['converged']}\n",
        encoding="utf-8",
    )
    print(subtype, "tensor", f"{elapsed:.3f}s", result["iterations"], result["converged"], flush=True)


def _build_one_cpu(task):
    folder_s, net_id, n_comp, q = task
    from pathlib import Path as P

    import numpy as np
    from knk_accel.versions import pcnet_143 as pc

    folder = P(folder_s)
    genes_n = len((folder / "genes.txt").read_text(encoding="utf-8").splitlines())
    raw = np.fromfile(folder / "cpm.bin", dtype=np.float64)
    counts = raw.reshape((genes_n, raw.size // genes_n), order="F")
    text = (folder / f"net_{net_id:02d}_indices.txt").read_text(encoding="utf-8").split()
    idx = np.asarray([int(x) for x in text], dtype=np.int64)
    started = time.perf_counter()
    network = pc(counts[:, idx], n_comp=n_comp, q=q, device="cpu")
    elapsed = time.perf_counter() - started
    import scipy.sparse as sp

    csr = sp.csr_matrix(np.asarray(network))
    with (folder / f"gpu_net_{net_id:02d}.csr").open("wb") as handle:
        np.asarray([csr.shape[0], csr.shape[1], csr.nnz], dtype=np.int32).tofile(handle)
        np.asarray(csr.indptr, dtype=np.int32).tofile(handle)
        np.asarray(csr.indices, dtype=np.int32).tofile(handle)
        np.asarray(csr.data, dtype=np.float64).tofile(handle)
    print("cpu net", net_id, f"{elapsed:.3f}s", flush=True)
    return elapsed


def main() -> int:
    env_path = config.RESULT_DIR / "_跨亚群" / "运行配置_run.env"
    plan = probe_mod.read_env_file(env_path)
    plan["cuda"] = plan.get("cuda", "True") == "True"
    plan["net_workers"] = int(plan.get("net_workers", 1))
    plan["rscript"] = plan.get("rscript") or probe_mod.find_rscript()
    for subtype in config.SUBTYPES:
        one_subtype(subtype, plan)
    print("STEP2_DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
