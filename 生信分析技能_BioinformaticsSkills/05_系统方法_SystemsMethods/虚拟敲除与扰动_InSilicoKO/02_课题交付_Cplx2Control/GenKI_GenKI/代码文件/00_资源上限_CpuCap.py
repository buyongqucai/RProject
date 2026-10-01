"""Cap GenKI CPU threads so Knk Formal and Windows keep cores.

Import and call apply() before numpy or torch work. This file does not
start training, GRN construction, or Ray Tune.

24 logical cores on this machine.
Windows reserve: 4.
While Formal is running: 2 threads, 1 Ray trial, train on GPU.
After Formal: 16 threads, at most 2 Ray trials.
"""

from __future__ import annotations

import os

THREADS_WHILE_FORMAL = 2
THREADS_AFTER_FORMAL = 16
RAY_WHILE_FORMAL = 1
RAY_AFTER_FORMAL = 2


def apply(formal_running: bool = True) -> int:
    """Set BLAS/OpenMP/PyTorch/Ray limits. Returns the CPU thread cap."""
    threads = THREADS_WHILE_FORMAL if formal_running else THREADS_AFTER_FORMAL
    ray_cpus = RAY_WHILE_FORMAL if formal_running else RAY_AFTER_FORMAL
    for key in (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        os.environ[key] = str(threads)
    os.environ["RAY_NUM_CPUS"] = str(ray_cpus)
    try:
        import torch

        torch.set_num_threads(threads)
        torch.set_num_interop_threads(1)
    except Exception:
        pass
    return threads
