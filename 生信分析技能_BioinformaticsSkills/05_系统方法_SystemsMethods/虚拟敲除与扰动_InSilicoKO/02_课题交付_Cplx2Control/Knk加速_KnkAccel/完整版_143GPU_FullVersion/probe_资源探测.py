"""资源探测与分配：先探测这台机器，再分配线程/并发/设备。

没有写死的核数、内存或显存数字。探测结果写入
<RESULT_DIR>/_跨亚群/资源探测与分配_ProbePlan.txt。
"""

from __future__ import annotations

import glob
import os
import shutil
from pathlib import Path


def find_rscript() -> str:
    env = os.environ.get("KNK_RSCRIPT")
    if env and Path(env).exists():
        return env
    hit = shutil.which("Rscript")
    if hit:
        return hit
    for root in (r"E:\R-*", r"C:\Program Files\R\R-*", r"C:\Program Files\R\*"):
        for folder in sorted(glob.glob(root), reverse=True):
            candidate = Path(folder) / "bin" / "Rscript.exe"
            if candidate.exists():
                return str(candidate)
    raise RuntimeError("Rscript not found; set KNK_RSCRIPT")


def find_cuda_bin() -> Path | None:
    env = os.environ.get("KNK_CUDA_BIN")
    if env and Path(env).is_dir():
        return Path(env)
    for key in ("CUDA_PATH", "CUDA_HOME"):
        value = os.environ.get(key)
        if value:
            for sub in ("bin/x64", "bin"):
                candidate = Path(value) / sub
                if candidate.is_dir():
                    return candidate
    try:
        from torch.utils.cpp_extension import CUDA_HOME

        if CUDA_HOME:
            for sub in ("bin/x64", "bin"):
                candidate = Path(CUDA_HOME) / sub
                if candidate.is_dir():
                    return candidate
    except Exception:
        pass
    for folder in sorted(glob.glob(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v*"), reverse=True):
        for sub in ("bin/x64", "bin"):
            candidate = Path(folder) / sub
            if candidate.is_dir():
                return candidate
    return None


def probe(n_samples: int, n_genes: int, n_jobs: int) -> dict:
    """探测 CPU / 内存 / GPU，给出本机分配方案。"""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from knk_accel import resources

    cpu = resources.os_cpu_count()
    ram = resources.free_ram_bytes()
    plan: dict = {
        "cpu_total": cpu,
        "free_ram_gb": round(ram / 1024**3, 1),
        "rscript": find_rscript(),
        "cuda_bin": str(find_cuda_bin() or ""),
    }
    # 留 2 个逻辑核给系统；BLAS 固定 1 线程，靠并发吃满机器。
    plan["host_threads"] = max(1, cpu - 2)
    plan["blas_threads"] = 1
    plan["r_threads"] = max(1, cpu - 2)
    try:
        import torch

        plan["cuda"] = bool(torch.cuda.is_available())
        plan["gpu_name"] = torch.cuda.get_device_name(0) if plan["cuda"] else ""
    except Exception:
        plan["cuda"] = False
        plan["gpu_name"] = ""
    if plan["cuda"]:
        gpu_plan = resources.plan_gpu_network_concurrency(n_samples, n_genes, n_jobs)
        plan["gpu"] = gpu_plan
        plan["net_workers"] = max(1, int(gpu_plan["concurrency"]))
    else:
        cpu_plan = resources.plan_cpu_workers(n_samples, n_genes, n_jobs)
        plan["cpu"] = cpu_plan
        plan["net_workers"] = max(1, int(cpu_plan["workers"]))
    return plan


def format_plan(plan: dict) -> str:
    lines = ["# 资源探测与分配（运行时生成，不写死）"]
    for key in (
        "cpu_total", "free_ram_gb", "host_threads", "blas_threads",
        "r_threads", "net_workers", "cuda", "gpu_name", "rscript", "cuda_bin",
    ):
        lines.append(f"{key}={plan.get(key)}")
    for section in ("gpu", "cpu"):
        if section in plan:
            for key, value in plan[section].items():
                lines.append(f"{section}.{key}={value}")
    return "\n".join(lines) + "\n"


def export_env_file(path: Path, plan: dict, c) -> None:
    """给 R 步骤的 KEY=VALUE 配置。"""
    pairs = {
        "RAW_DIR": str(c.DATA_DIR),
        "RESULT_DIR": str(c.RESULT_DIR),
        "META_FILE": c.META_FILE,
        "COUNTS_FILE": c.COUNTS_FILE,
        "MODEL_COL": c.MODEL_COL,
        "MODEL_VAL": c.MODEL_VAL,
        "SUBTYPE_COL": c.SUBTYPE_COL,
        "CELL_ID_COL": c.CELL_ID_COL,
        "SUBTYPES": ",".join(c.SUBTYPES),
        "KNOCK_GENES": ",".join(c.KNOCK_GENES),
        "N_NET": c.N_NET,
        "N_CELLS": c.N_CELLS,
        "MIN_LIB_SIZE": c.MIN_LIB_SIZE,
        "MIN_PCT": c.MIN_PCT,
        "MAX_MT_RATIO": c.MAX_MT_RATIO,
        "MIN_DETECTED": c.MIN_DETECTED,
        "N_COMP": c.N_COMP,
        "Q": c.Q,
        "SEED": c.SEED,
        "N_DECIMAL": c.N_DECIMAL,
        "FDR_CUT": c.FDR_CUT,
        "KO_ALIGN_D": c.KO_ALIGN_D,
        "ENRICH_P": c.ENRICH_P,
        "ENRICH_Q": c.ENRICH_Q,
        "R_THREADS": plan.get("r_threads", 2),
        "CUDA": plan.get("cuda", False),
        "NET_WORKERS": plan.get("net_workers", 1),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"{k}={v}" for k, v in pairs.items()) + "\n", encoding="utf-8")


def read_env_file(path: Path) -> dict:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip()
    return out
