"""Detect this machine and reserve a slice for the OS before GenKI runs.

Call prepare() or run this file before importing NumPy or PyTorch.
No CPU count, RAM size, or GPU name is hardcoded. The same rules apply on
the next computer.

Rules:
- RAM reserve is 25% of physical memory, clamped to 4–8 GB.
- If the chosen GPU is driving a display, VRAM reserve is 15%, clamped to 0.5–1.5 GB.
- CPU reserve is 1 thread when the machine has 8 or fewer, otherwise 2.
- GRN uses every remaining thread, one BLAS thread per worker.
- Search runs as many trials as fit in the remaining VRAM (at least 1 GB each)
  and the remaining threads (at least 2 each).
- The final fit uses one process and all remaining threads.
"""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
from pathlib import Path

RAM_RESERVE_FRACTION = 0.25
RAM_RESERVE_MIN_GB = 4.0
RAM_RESERVE_MAX_GB = 8.0
VRAM_RESERVE_FRACTION = 0.15
VRAM_RESERVE_MIN_GB = 0.5
VRAM_RESERVE_MAX_GB = 1.5
MIN_VRAM_PER_TRIAL_GB = 1.0
MIN_THREADS_PER_TRIAL = 2


def detect() -> dict:
    """Read logical CPUs, physical RAM, and NVIDIA GPUs. Does not load PyTorch."""
    gpus = _detect_gpus()
    return {
        "logical_cpus": os.cpu_count() or 1,
        "ram_gb": _detect_ram_gb(),
        "gpus": gpus,
        "gpu": _choose_gpu(gpus),
    }


def allocate(hardware: dict) -> dict:
    """Turn a detect() result into per-phase thread and memory limits."""
    logical = max(1, int(hardware["logical_cpus"]))
    ram_gb = float(hardware["ram_gb"])
    cpu_reserve = 1 if logical <= 8 else 2
    job_cpus = max(1, logical - cpu_reserve)
    ram_reserve = min(RAM_RESERVE_MAX_GB, max(RAM_RESERVE_MIN_GB, ram_gb * RAM_RESERVE_FRACTION))
    ram_job = max(0.0, ram_gb - ram_reserve)
    gpu = hardware.get("gpu")
    if gpu is None:
        vram_gb = 0.0
        display = False
        vram_reserve = 0.0
        gpu_index = None
        gpu_name = ""
    else:
        vram_gb = float(gpu["vram_gb"])
        display = bool(gpu["display"])
        vram_reserve = (
            min(VRAM_RESERVE_MAX_GB, max(VRAM_RESERVE_MIN_GB, vram_gb * VRAM_RESERVE_FRACTION))
            if display
            else 0.0
        )
        gpu_index = int(gpu["index"])
        gpu_name = str(gpu["name"])
    vram_job = max(0.0, vram_gb - vram_reserve)
    if vram_job >= MIN_VRAM_PER_TRIAL_GB:
        by_vram = int(vram_job // MIN_VRAM_PER_TRIAL_GB)
        by_cpu = max(1, job_cpus // MIN_THREADS_PER_TRIAL)
        trials = max(1, min(by_vram, by_cpu))
    else:
        trials = 1
    threads_per_trial = max(1, job_cpus // trials)
    vram_per_trial = (vram_job / trials) if trials else 0.0
    return {
        "hardware": {
            "logical_cpus": logical,
            "ram_gb": ram_gb,
            "gpu_index": gpu_index,
            "gpu_name": gpu_name,
            "vram_gb": vram_gb,
            "display_gpu": display,
        },
        "reserve": {
            "cpu_threads": cpu_reserve,
            "ram_gb": ram_reserve,
            "vram_gb": vram_reserve,
        },
        "job_cpus": job_cpus,
        "ram_for_genki_gb": ram_job,
        "vram_for_genki_gb": vram_job,
        "grn": {"workers": job_cpus, "threads_per_worker": 1},
        "search": {
            "trials": trials,
            "threads_per_trial": threads_per_trial,
            "gpu_per_trial": (1.0 / trials) if vram_gb else 0.0,
            "vram_per_trial_gb": vram_per_trial,
        },
        "fit": {"threads": job_cpus, "vram_gb": vram_job},
    }


def prepare(phase: str = "search", bind_device: bool = True, hardware: dict | None = None) -> dict:
    """Detect, allocate, and apply one phase. Returns the full plan."""
    plan = allocate(hardware if hardware is not None else detect())
    _apply_phase(plan, phase, bind_device)
    plan["phase"] = phase
    return plan


def format_plan(plan: dict) -> str:
    hw = plan["hardware"]
    reserve = plan["reserve"]
    search = plan["search"]
    gpu_line = (
        f"{hw['gpu_name']}  {hw['vram_gb']:.1f} GB  显示输出={'是' if hw['display_gpu'] else '否'}"
        if hw["gpu_name"]
        else "未检测到 NVIDIA 显卡，搜索和训练用 CPU"
    )
    lines = [
        "GenKI 资源分配（开跑前探测）",
        f"CPU 逻辑线程 {hw['logical_cpus']}，留给系统 {reserve['cpu_threads']}，算法 {plan['job_cpus']}",
        f"内存 {hw['ram_gb']:.1f} GB，留给系统 {reserve['ram_gb']:.1f} GB，算法 {plan['ram_for_genki_gb']:.1f} GB",
        f"GPU {gpu_line}",
        f"显存留给系统 {reserve['vram_gb']:.1f} GB，算法 {plan['vram_for_genki_gb']:.1f} GB",
        f"建网 grn：{plan['grn']['workers']} 个进程，每个 {plan['grn']['threads_per_worker']} 个线程，不用 GPU",
        (
            f"搜索 search：同时 {search['trials']} 个 trial，每个 {search['threads_per_trial']} 个线程，"
            f"每个 num_gpus={search['gpu_per_trial']:.3f}，显存上限 {search['vram_per_trial_gb']:.1f} GB"
        ),
        f"正式训练 fit：1 个进程，{plan['fit']['threads']} 个线程，显存上限 {plan['fit']['vram_gb']:.1f} GB",
    ]
    return "\n".join(lines) + "\n"


def _apply_phase(plan: dict, phase: str, bind_device: bool) -> None:
    if phase not in ("grn", "search", "fit"):
        raise ValueError("phase must be grn, search, or fit")
    if phase == "grn":
        threads = plan["grn"]["threads_per_worker"]
        ray_cpus = plan["grn"]["workers"]
        vram_gb = 0.0
    elif phase == "search":
        threads = plan["search"]["threads_per_trial"]
        ray_cpus = plan["job_cpus"]
        vram_gb = plan["search"]["vram_per_trial_gb"]
    else:
        threads = plan["fit"]["threads"]
        ray_cpus = 1
        vram_gb = plan["fit"]["vram_gb"]
    total_vram = float(plan["hardware"]["vram_gb"])
    fraction = 0.0 if total_vram <= 0 else min(1.0, vram_gb / total_vram)
    for key in (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        os.environ[key] = str(threads)
    os.environ["RAY_NUM_CPUS"] = str(ray_cpus)
    os.environ["GENKI_PHASE"] = phase
    os.environ["GENKI_JOB_CPUS"] = str(plan["job_cpus"])
    os.environ["GENKI_GRN_WORKERS"] = str(plan["grn"]["workers"])
    os.environ["GENKI_SEARCH_TRIALS"] = str(plan["search"]["trials"])
    os.environ["GENKI_TRIAL_CPUS"] = str(plan["search"]["threads_per_trial"])
    os.environ["GENKI_TRIAL_GPUS"] = f"{plan['search']['gpu_per_trial']:.4f}"
    os.environ["GENKI_CUDA_MEM_FRACTION"] = f"{fraction:.4f}"
    if plan["hardware"]["gpu_index"] is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = str(plan["hardware"]["gpu_index"])
    if bind_device and phase != "grn" and fraction > 0:
        _bind_torch(threads, fraction)


def _bind_torch(threads: int, fraction: float) -> None:
    try:
        import torch
    except Exception:
        return
    torch.set_num_threads(threads)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    if fraction > 0 and torch.cuda.is_available():
        torch.cuda.set_per_process_memory_fraction(fraction)


def _detect_ram_gb() -> float:
    if os.name == "nt":
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MEMORYSTATUSEX()
        status.dwLength = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            raise OSError("GlobalMemoryStatusEx failed")
        return status.ullTotalPhys / (1024**3)
    pages = os.sysconf("SC_PHYS_PAGES")
    page_size = os.sysconf("SC_PAGE_SIZE")
    return (pages * page_size) / (1024**3)


def _detect_gpus() -> list[dict]:
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,display_active",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    if completed.returncode != 0:
        return []
    gpus = []
    for line in completed.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 4:
            continue
        try:
            gpus.append(
                {
                    "index": int(parts[0]),
                    "name": parts[1],
                    "vram_gb": float(parts[2]) / 1024.0,
                    "display": parts[3].lower() in ("enabled", "on", "true", "1"),
                }
            )
        except ValueError:
            continue
    return gpus


def _choose_gpu(gpus: list[dict]) -> dict | None:
    if not gpus:
        return None
    compute_only = [gpu for gpu in gpus if not gpu["display"]]
    pool = compute_only or gpus
    return max(pool, key=lambda gpu: gpu["vram_gb"])


def _self_test() -> None:
    desktop = allocate(
        {"logical_cpus": 12, "ram_gb": 32, "gpu": {"index": 0, "name": "RTX 4060", "vram_gb": 8, "display": True}}
    )
    assert desktop["reserve"]["cpu_threads"] == 2
    assert desktop["job_cpus"] == 10
    assert abs(desktop["reserve"]["ram_gb"] - 8.0) < 1e-6
    assert abs(desktop["reserve"]["vram_gb"] - 1.2) < 1e-6
    assert desktop["search"]["trials"] == 5
    assert desktop["grn"]["workers"] == 10
    headless = allocate(
        {"logical_cpus": 24, "ram_gb": 48, "gpu": {"index": 0, "name": "RTX 4080 SUPER", "vram_gb": 16, "display": False}}
    )
    assert headless["reserve"]["vram_gb"] == 0.0
    assert headless["job_cpus"] == 22
    assert headless["search"]["trials"] == 11
    small = allocate({"logical_cpus": 4, "ram_gb": 16, "gpu": None})
    assert small["reserve"]["cpu_threads"] == 1
    assert small["job_cpus"] == 3
    assert small["search"]["trials"] == 1
    assert "未检测到" in format_plan(small)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--self-test" in args:
        _self_test()
        print("self-test ok")
        return 0
    plan = prepare("search", bind_device=False)
    text = format_plan(plan)
    sys.stdout.write(text)
    if "--out" in args:
        destination = Path(args[args.index("--out") + 1])
        destination.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
