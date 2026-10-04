"""1.4.3 GPU networks and sparse CP for PEP and NF1. One wild-type per subtype."""

import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from scipy import sparse

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE))
from knk_accel.cp_decomp import tensor_from_networks_gpu
from knk_accel.versions import pcnet_143

DESK = Path(r"C:\Users\10540\Desktop\琪乐无穷\虚拟敲除")
ALGO = "scTenifoldKnk_1.4.3_GPU"
RSCRIPT = r"E:\R-4.6.0\bin\Rscript.exe"
SUBTYPES = ("PEP", "NF1")


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


def r_init(folder: Path, n_gene: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    script = folder / "_init.R"
    script.write_text(
        "\n".join([
            "args <- commandArgs(trailingOnly=TRUE)",
            "out <- args[[1]]; n <- as.integer(args[[2]])",
            "set.seed(1)",
            "writeBin(as.numeric(matrix(rnorm(n*3), n, 3)), file(file.path(out,'u1.bin'),'wb'))",
            "writeBin(as.numeric(matrix(rnorm(n*3), n, 3)), file(file.path(out,'u2.bin'),'wb'))",
            "writeBin(as.numeric(matrix(rnorm(10*3), 10, 3)), file(file.path(out,'u3.bin'),'wb'))",
        ]),
        encoding="utf-8",
    )
    subprocess.run([RSCRIPT, "--vanilla", str(script), str(folder), str(n_gene)], check=True)
    u1 = np.fromfile(folder / "u1.bin", dtype=np.float64).reshape((n_gene, 3), order="F")
    u2 = np.fromfile(folder / "u2.bin", dtype=np.float64).reshape((n_gene, 3), order="F")
    u3 = np.fromfile(folder / "u3.bin", dtype=np.float64).reshape((10, 3), order="F")
    return u1, u2, u3


def one_subtype(subtype: str) -> None:
    folder = DESK / "结果文件" / subtype / ALGO / "_野生型" / "数据文件"
    note = DESK / "结果文件" / subtype / ALGO / "_野生型" / "报告文件"
    note.mkdir(parents=True, exist_ok=True)
    counts, genes = load_cpm(folder)
    lines = ["net,seconds,genes"]
    for net_id in range(1, 11):
        path = folder / f"gpu_net_{net_id:02d}.csr"
        if path.exists() and path.stat().st_size > 1000:
            print(subtype, "skip", net_id, flush=True)
            continue
        started = time.perf_counter()
        network = pcnet_143(counts[:, load_indices(folder, net_id)], n_comp=3, q=0.9, device="gpu")
        elapsed = time.perf_counter() - started
        write_csr(path, np.asarray(network))
        lines.append(f"{net_id},{elapsed:.3f},{len(genes)}")
        print(subtype, "gpu net", net_id, f"{elapsed:.3f}", flush=True)
        del network
    (note / "gpu_network_times.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    nets = [read_csr(folder / f"gpu_net_{i:02d}.csr") for i in range(1, 11)]
    init = r_init(folder, len(genes))
    started = time.perf_counter()
    result = tensor_from_networks_gpu(nets, init, n_comp=3, max_iter=1000, tol=1e-5, n_decimal=3)
    elapsed = time.perf_counter() - started
    matrix = np.asarray(result["matrix"])
    matrix.tofile(folder / "gpu_wt_rounded.bin")
    (note / "gpu_tensor.txt").write_text(
        f"seconds={elapsed:.3f}\niterations={result['iterations']}\nconverged={result['converged']}\n",
        encoding="utf-8",
    )
    print(subtype, "tensor", f"{elapsed:.3f}", result["iterations"], result["converged"], flush=True)


def main() -> None:
    for subtype in SUBTYPES:
        one_subtype(subtype)
    print("GPU_DONE", flush=True)


if __name__ == "__main__":
    main()
