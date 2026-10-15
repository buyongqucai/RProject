# -*- coding: utf-8 -*-
"""Generate KEGG bio-structure base illustrations on local NVIDIA GPU (RTX).

Default backend for bio-structure-animation skill when CUDA is available.
Much faster than cloud GenerateImage for batch ranks 089–183 / FLAG_TOP regen.

Install (once):
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
  pip install diffusers transformers accelerate safetensors pillow pandas

Usage:
  # single
  python 45_local_sd_bases.py --rank 88 --pid hsa04920 --prompt "..."

  # batch from KEGG list (ranks without base, or --force)
  python 45_local_sd_bases.py --batch 97 120
  python 45_local_sd_bases.py --batch-flagged   # from _audit_edge_clip.csv FLAG_TOP

RTX 4060 8GB defaults: SDXL 1024×576 fp16 + attention slicing + VAE tiling.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(r"E:/RProject/努力学习项目/网络药理学")
CODE = ROOT / "代码文件"
OUT = ROOT / "交付文件" / "图片" / "动画_生物结构" / "_bases"
ASSETS = Path(r"C:/Users/10540/.cursor/projects/e-RProject/assets")
MAN = ROOT / "交付文件" / "图片/KEGG官方通路图/00_全部通路图清单.csv"
AUDIT = ROOT / "交付文件" / "图片" / "动画_生物结构" / "_audit_edge_clip.csv"
PROMPT_DIR = CODE / "_gpu_prompts"

sys.path.insert(0, str(CODE))

FORBIDDEN = (
    "Medical histology animation, cinematic 3D organelles, landscape 16:9. "
    "Short English labels on structures. No title banner or UI chrome. "
    "Full subject in frame with 6% margins, no edge cropping."
)

NEG = (
    "pathway title banner, dark header, white title strip, step panels, UI, watermark, "
    "cropped edges, flowchart boxes, flat icons, low detail, blank unlabeled diagram"
)


def default_prompt(pid: str, en: str, zh: str) -> str:
    # Keep short: SDXL CLIP truncates ~77 tokens on first encoder
    return (
        f"Medical animation of human pathway {pid} {en}. "
        f"Realistic cells, membrane receptors, mitochondria, nucleus, signal flow. "
        f"English labels on key structures. Teal cream histology. {FORBIDDEN}"
    )


def load_zh():
    try:
        from kegg_zh_names import ZH

        return ZH
    except Exception:
        return {}


def ensure_pipe(model_id: str, steps_hint: int = 24):
    import torch
    from diffusers import StableDiffusionXLPipeline

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA not available")

    dtype = torch.float16
    print(f"GPU: {torch.cuda.get_device_name(0)} | VRAM free check...", flush=True)
    pipe = StableDiffusionXLPipeline.from_pretrained(
        model_id,
        torch_dtype=dtype,
        variant="fp16",
        use_safetensors=True,
    )
    pipe.enable_attention_slicing()
    try:
        pipe.enable_vae_tiling()
    except Exception:
        pass
    try:
        pipe.enable_model_cpu_offload()  # safer on 8GB; still uses GPU for UNet
        print("pipeline: model_cpu_offload (8GB-safe)", flush=True)
    except Exception:
        pipe = pipe.to("cuda")
        print("pipeline: full CUDA", flush=True)
    return pipe


def gen_one(pipe, prompt: str, width: int, height: int, steps: int, guidance: float, seed: int | None):
    import torch

    # SDXL: put FULL text into both encoders — never privately shorten the prompt.
    # prompt (CLIP) + prompt_2 (OpenCLIP) both receive the complete string.
    g = None
    if seed is not None:
        g = torch.Generator(device="cpu").manual_seed(seed)
    try:
        img = pipe(
            prompt=prompt,
            prompt_2=prompt,
            negative_prompt=NEG,
            negative_prompt_2=NEG,
            num_inference_steps=steps,
            guidance_scale=guidance,
            width=width,
            height=height,
            generator=g,
            truncation=False,
        ).images[0]
    except TypeError:
        # older diffusers without truncation kw
        img = pipe(
            prompt=prompt,
            prompt_2=prompt,
            negative_prompt=NEG,
            negative_prompt_2=NEG,
            num_inference_steps=steps,
            guidance_scale=guidance,
            width=width,
            height=height,
            generator=g,
        ).images[0]
    except RuntimeError as e:
        if "CUDA out of memory" in str(e) and width > 768:
            torch.cuda.empty_cache()
            w2, h2 = 768, 432
            print(f"OOM -> retry {w2}x{h2} (prompt unchanged)", flush=True)
            img = pipe(
                prompt=prompt,
                prompt_2=prompt,
                negative_prompt=NEG,
                negative_prompt_2=NEG,
                num_inference_steps=steps,
                guidance_scale=guidance,
                width=w2,
                height=h2,
                generator=g,
            ).images[0]
        else:
            raise
    return img


def save_base(img, rank: int, pid: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    name = f"bio_base_{rank:03d}_{pid}.png"
    for d in (OUT, ASSETS):
        p = d / name
        img.save(p)
    print("WROTE", OUT / name, flush=True)
    return OUT / name


def resolve_prompt(rank: int, pid: str, en: str, zh: str, prompt: str, prompt_file: str) -> str:
    if prompt_file:
        return Path(prompt_file).read_text(encoding="utf-8").strip()
    if prompt:
        return prompt.strip()
    pf = PROMPT_DIR / f"{rank:03d}_{pid}.txt"
    if pf.exists():
        return pf.read_text(encoding="utf-8").strip()
    return default_prompt(pid, en, zh)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rank", type=int, default=None)
    ap.add_argument("--pid", default="")
    ap.add_argument("--prompt", default="")
    ap.add_argument("--prompt-file", default="")
    ap.add_argument("--batch", nargs=2, type=int, metavar=("START", "END"))
    ap.add_argument("--batch-flagged", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--steps", type=int, default=24)
    ap.add_argument("--guidance", type=float, default=6.5)
    # 4060 8GB-safe default (16:9). Upscale later via prepare_base letterbox.
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=576)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument(
        "--model",
        default="stabilityai/stable-diffusion-xl-base-1.0",
        help="HF model id (cached after first download)",
    )
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

    try:
        import torch  # noqa: F401
        from diffusers import StableDiffusionXLPipeline  # noqa: F401
    except ImportError:
        print(
            "MISSING torch/diffusers. Install:\n"
            "  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124\n"
            "  pip install diffusers transformers accelerate safetensors pillow pandas\n",
            file=sys.stderr,
        )
        sys.exit(1)

    import torch

    if not torch.cuda.is_available():
        print("CUDA not available — install CUDA torch wheels.", file=sys.stderr)
        sys.exit(1)

    ZH = load_zh()
    jobs: list[tuple[int, str, str, str]] = []

    if args.batch_flagged:
        if not AUDIT.exists():
            print("Run 44_audit_edge_clip.py first", file=sys.stderr)
            sys.exit(1)
        with AUDIT.open(encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if int(row.get("flag_top", 0)) == 1 and row.get("pid"):
                    rank = int(row["rank"])
                    pid = row["pid"]
                    jobs.append((rank, pid, pid, ZH.get(pid, pid)))
        # enrich EN from MAN
        if MAN.exists():
            import pandas as pd

            df = pd.read_csv(MAN, encoding="utf-8-sig")
            emap = {int(r["rank"]): str(r["description"]) for _, r in df.iterrows()}
            jobs = [(r, p, emap.get(r, e), ZH.get(p, z)) for r, p, e, z in jobs]
    elif args.batch:
        import pandas as pd

        start, end = args.batch
        df = pd.read_csv(MAN, encoding="utf-8-sig")
        for _, r in df.iterrows():
            rank = int(r["rank"])
            if rank < start or rank > end:
                continue
            pid = str(r["pathway_id"]).strip()
            en = str(r["description"]).strip()
            zh = ZH.get(pid, en[:20])
            jobs.append((rank, pid, en, zh))
    elif args.rank is not None and args.pid:
        en = args.pid
        zh = ZH.get(args.pid, args.pid)
        if MAN.exists():
            import pandas as pd

            df = pd.read_csv(MAN, encoding="utf-8-sig")
            hit = df[df["rank"] == args.rank]
            if len(hit):
                en = str(hit.iloc[0]["description"])
                zh = ZH.get(args.pid, en[:20])
        jobs.append((args.rank, args.pid, en, zh))
    else:
        print("Need --rank/--pid, or --batch START END, or --batch-flagged", file=sys.stderr)
        sys.exit(1)

    pipe = ensure_pipe(args.model)
    n_ok = n_skip = 0
    for rank, pid, en, zh in jobs:
        dest = OUT / f"bio_base_{rank:03d}_{pid}.png"
        if dest.exists() and not args.force and not args.batch_flagged:
            print("SKIP exists", dest.name, flush=True)
            n_skip += 1
            continue
        prompt = resolve_prompt(rank, pid, en, zh, args.prompt, args.prompt_file)
        if FORBIDDEN not in prompt:
            prompt = f"{prompt}\n{FORBIDDEN}"
        print(f"GEN {rank:03d} {pid} {args.width}x{args.height} steps={args.steps}", flush=True)
        img = gen_one(pipe, prompt, args.width, args.height, args.steps, args.guidance, args.seed + rank)
        save_base(img, rank, pid)
        n_ok += 1
        try:
            torch.cuda.empty_cache()
        except Exception:
            pass

    print(f"DONE ok={n_ok} skip={n_skip}", flush=True)


if __name__ == "__main__":
    main()
