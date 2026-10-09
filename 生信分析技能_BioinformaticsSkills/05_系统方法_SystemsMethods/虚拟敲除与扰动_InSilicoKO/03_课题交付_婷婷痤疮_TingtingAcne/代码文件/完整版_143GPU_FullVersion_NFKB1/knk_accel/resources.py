"""Decide concurrency from this machine, not from a fixed network count.

GPU: time one gesvd against several concurrent copies of the same shape.
Add another network only when jobs per second rise and the copy still fits
in free VRAM and free host RAM. CPU: one process while several Rscript
processes are already running; otherwise use free cores and free RAM.
"""

from __future__ import annotations

import ctypes
import subprocess
import time

# A new stream has to beat the current jobs/second by this much.
MIN_RATE_GAIN = 1.10
# Fraction of currently free memory the probe is allowed to fill.
USABLE_FRACTION = 0.75


def free_ram_bytes() -> int:
    class MemoryStatus(ctypes.Structure):
        _fields_ = (
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        )

    status = MemoryStatus()
    status.dwLength = ctypes.sizeof(status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return 0
    return int(status.ullAvailPhys)


def rscript_count() -> int:
    try:
        output = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq Rscript.exe", "/FO", "CSV", "/NH"],
            text=True,
            errors="replace",
        )
    except (OSError, subprocess.CalledProcessError):
        return 0
    return sum(1 for line in output.splitlines() if "Rscript" in line)


def plan_cpu_workers(n_samples: int, n_genes: int, n_jobs: int) -> dict:
    """How many CPU processes to use for one network's genes."""
    cpus = os_cpu_count()
    running = rscript_count()
    matrix_bytes = max(1, int(n_samples) * int(n_genes) * 8 * 3)
    by_ram = max(1, int(free_ram_bytes() * USABLE_FRACTION) // matrix_bytes)
    # Leave two cores for the OS. A live Formal job already owns several Rscript processes.
    by_cpu = 1 if running >= 4 else max(1, cpus - 2)
    workers = max(1, min(int(n_jobs), by_cpu, by_ram, max(1, int(n_genes) // 8)))
    return {
        "workers": workers,
        "cpus": cpus,
        "rscript": running,
        "free_ram": free_ram_bytes(),
        "reason": "rscript" if running >= 4 else "cpu_and_ram",
    }


def os_cpu_count() -> int:
    import os

    return max(1, int(os.cpu_count() or 1))


def _time_concurrent(n_samples: int, n_cols: int, k: int) -> float:
    import torch

    from knk_accel.pcnet import GPU_SVD_DRIVER

    torch.set_num_threads(1)
    matrices = [
        torch.randn(n_samples, n_cols, device="cuda", dtype=torch.float64)
        for _ in range(k)
    ]
    streams = [torch.cuda.Stream() for _ in range(k)]
    torch.cuda.synchronize()
    started = time.perf_counter()
    for matrix, stream in zip(matrices, streams):
        with torch.cuda.stream(stream):
            torch.linalg.svd(matrix, full_matrices=False, driver=GPU_SVD_DRIVER)
    for stream in streams:
        stream.synchronize()
    elapsed = time.perf_counter() - started
    del matrices
    return elapsed


def plan_gpu_network_concurrency(n_samples: int, n_genes: int, n_jobs: int) -> dict:
    """How many networks to run at once on the selected GPU."""
    import torch

    n_jobs = max(1, int(n_jobs))
    n_cols = int(n_genes) - 1
    if n_jobs == 1 or n_samples < 2 or n_cols < 2 or not torch.cuda.is_available():
        return {
            "concurrency": 1,
            "free_vram": 0,
            "peak_bytes": 0,
            "free_ram": free_ram_bytes(),
            "device": "",
            "probed_k": 1,
            "reason": "single",
        }
    free_vram, total_vram = torch.cuda.mem_get_info()
    name = torch.cuda.get_device_name(0)
    try:
        _time_concurrent(int(n_samples), n_cols, 1)
    except RuntimeError:
        torch.cuda.empty_cache()
        return {
            "concurrency": 1,
            "free_vram": int(free_vram),
            "peak_bytes": 0,
            "free_ram": free_ram_bytes(),
            "device": name,
            "probed_k": 1,
            "reason": "probe_failed",
        }
    torch.cuda.reset_peak_memory_stats()
    baseline = torch.cuda.memory_allocated()
    try:
        serial = _time_concurrent(int(n_samples), n_cols, 1)
    except RuntimeError:
        torch.cuda.empty_cache()
        return {
            "concurrency": 1,
            "free_vram": int(free_vram),
            "peak_bytes": 0,
            "free_ram": free_ram_bytes(),
            "device": name,
            "probed_k": 1,
            "reason": "probe_failed",
        }
    peak = max(1, int(torch.cuda.max_memory_allocated() - baseline))
    coef_bytes = max(1, int(n_genes) * n_cols * 8)
    usable_vram = int(free_vram * USABLE_FRACTION)
    usable_ram = int(free_ram_bytes() * USABLE_FRACTION)
    limit = max(1, min(n_jobs, usable_vram // peak, max(1, usable_ram // coef_bytes)))
    chosen = 1
    rate = 1.0 / serial
    probed = 1
    reason = "no_gain"
    trials = [f"1:{serial:.3f}"]
    k = 2
    while k <= limit:
        try:
            elapsed = _time_concurrent(int(n_samples), n_cols, k)
        except RuntimeError:
            reason = "oom"
            break
        probed = k
        trials.append(f"{k}:{elapsed:.3f}")
        new_rate = k / elapsed
        if new_rate < rate * MIN_RATE_GAIN:
            reason = "plateau" if chosen > 1 else "no_gain"
            break
        chosen = k
        rate = new_rate
        reason = "faster"
        k += 1
    torch.cuda.empty_cache()
    return {
        "concurrency": chosen,
        "free_vram": int(free_vram),
        "total_vram": int(total_vram),
        "peak_bytes": peak,
        "free_ram": free_ram_bytes(),
        "device": name,
        "probed_k": probed,
        "serial_s": serial,
        "trials": " ".join(trials),
        "reason": reason,
    }
