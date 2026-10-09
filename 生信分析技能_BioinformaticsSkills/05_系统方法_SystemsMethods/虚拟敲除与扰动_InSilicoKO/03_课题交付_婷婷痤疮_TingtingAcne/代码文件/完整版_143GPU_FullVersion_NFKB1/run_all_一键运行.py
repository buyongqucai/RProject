"""完整版 1.4.3 GPU —— 一键运行。

流程：探测资源 → 导出+质控（R）→ 1.4.3 建网+张量（GPU/CPU 自动）→ 敲除+富集（R）。
换数据集只需改 config_配置.py 里的 DATA_DIR 与 RESULT_DIR。
每步都可重复运行：已有产物自动跳过。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import config_配置 as config  # noqa: E402
import probe_资源探测 as probe_mod  # noqa: E402


def run_r(script: str, env_path: Path, rscript: str) -> None:
    print(f"== {script} ==", flush=True)
    completed = subprocess.run(
        [rscript, "--vanilla", str(HERE / script), str(env_path)],
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise SystemExit(f"{script} failed with {completed.returncode}")


def main() -> int:
    # 0) 先探测一次（基因数未知时用 3000 估计），把线程写进 env
    plan = probe_mod.probe(n_samples=config.N_CELLS, n_genes=3000, n_jobs=config.N_NET)
    env_path = config.RESULT_DIR / "run_config.env"
    probe_mod.export_env_file(env_path, plan, config)
    rscript = plan["rscript"]
    print(probe_mod.format_plan(plan), flush=True)

    # 1) 导出 + 质控 + 抽样（R）
    run_r("step1_export_qc.R", env_path, rscript)

    # 2) 基因数已知，重探测建网并发，再建网 + 张量
    n_genes = 3000
    for subtype in config.SUBTYPES:
        genes_file = config.RESULT_DIR / subtype / "scTenifoldKnk_1.4.3_GPU" / "WT" / "data" / "genes.txt"
        if genes_file.exists():
            n_genes = max(n_genes, len(genes_file.read_text(encoding="utf-8").splitlines()))
    plan = probe_mod.probe(n_samples=min(config.N_CELLS, 10**6), n_genes=n_genes, n_jobs=config.N_NET)
    probe_mod.export_env_file(env_path, plan, config)
    probe_txt = config.RESULT_DIR / "cross" / "probe_plan.txt"
    probe_txt.parent.mkdir(parents=True, exist_ok=True)
    probe_txt.write_text(probe_mod.format_plan(plan), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(HERE / "step2_gpu_build.py")],
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise SystemExit(f"step2 failed with {completed.returncode}")

    # 3) 敲除 + 富集（R）
    run_r("step3_ko_enrich.R", env_path, rscript)
    print("ALL_DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
