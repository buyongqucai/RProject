"""Compile an NVRTC kernel once per machine and reuse the cubin file.

A cached PTX still costs a driver JIT on every new process. The cubin is
already machine code for this GPU, so the next process only loads it.
"""

from __future__ import annotations

import ctypes
import hashlib
import os
from pathlib import Path

import torch

_CUDA_BIN = Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2\bin\x64")
_NVRTC_NAME = "nvrtc64_130_0.dll"
_CACHE = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "knk_accel" / "cubin"
_LOADED: dict[tuple[str, bytes, str], tuple[ctypes.CDLL, ctypes.c_void_p]] = {}
_NVCUDA: ctypes.CDLL | None = None


def _nvcuda() -> ctypes.CDLL:
    global _NVCUDA
    if _NVCUDA is not None:
        return _NVCUDA
    os.add_dll_directory(str(_CUDA_BIN))
    loaded = ctypes.CDLL("nvcuda.dll")
    loaded.cuInit.argtypes = [ctypes.c_uint]
    loaded.cuInit.restype = ctypes.c_int
    loaded.cuModuleLoadData.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p]
    loaded.cuModuleLoadData.restype = ctypes.c_int
    loaded.cuModuleGetFunction.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p, ctypes.c_char_p]
    loaded.cuModuleGetFunction.restype = ctypes.c_int
    loaded.cuLaunchKernel.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint,
        ctypes.c_uint,
        ctypes.c_uint,
        ctypes.c_uint,
        ctypes.c_uint,
        ctypes.c_uint,
        ctypes.c_uint,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.c_void_p,
    ]
    loaded.cuLaunchKernel.restype = ctypes.c_int
    status = loaded.cuInit(0)
    if status != 0:
        raise RuntimeError(f"cuInit failed: {status}")
    _NVCUDA = loaded
    return loaded


def _compile(source: str, arch: str) -> bytes:
    os.add_dll_directory(str(_CUDA_BIN))
    nvrtc = ctypes.CDLL(str(_CUDA_BIN / _NVRTC_NAME))
    nvrtc.nvrtcCreateProgram.argtypes = [
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    nvrtc.nvrtcCreateProgram.restype = ctypes.c_int
    nvrtc.nvrtcCompileProgram.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_char_p)]
    nvrtc.nvrtcCompileProgram.restype = ctypes.c_int
    nvrtc.nvrtcGetProgramLogSize.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t)]
    nvrtc.nvrtcGetProgramLogSize.restype = ctypes.c_int
    nvrtc.nvrtcGetProgramLog.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    nvrtc.nvrtcGetProgramLog.restype = ctypes.c_int
    nvrtc.nvrtcGetCUBINSize.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t)]
    nvrtc.nvrtcGetCUBINSize.restype = ctypes.c_int
    nvrtc.nvrtcGetCUBIN.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    nvrtc.nvrtcGetCUBIN.restype = ctypes.c_int
    nvrtc.nvrtcDestroyProgram.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
    nvrtc.nvrtcDestroyProgram.restype = ctypes.c_int
    program = ctypes.c_void_p()
    status = nvrtc.nvrtcCreateProgram(ctypes.byref(program), source.encode("utf-8"), b"knk_kernel.cu", 0, None, None)
    if status != 0:
        raise RuntimeError(f"nvrtcCreateProgram failed: {status}")
    options = [b"--fmad=false", f"--gpu-architecture={arch}".encode()]
    option_array = (ctypes.c_char_p * len(options))(*options)
    status = nvrtc.nvrtcCompileProgram(program, len(options), option_array)
    log_size = ctypes.c_size_t()
    nvrtc.nvrtcGetProgramLogSize(program, ctypes.byref(log_size))
    log = ctypes.create_string_buffer(log_size.value)
    nvrtc.nvrtcGetProgramLog(program, log)
    if status != 0:
        nvrtc.nvrtcDestroyProgram(ctypes.byref(program))
        raise RuntimeError(log.value.decode("utf-8", errors="replace") or f"nvrtc compile failed: {status}")
    cubin_size = ctypes.c_size_t()
    nvrtc.nvrtcGetCUBINSize(program, ctypes.byref(cubin_size))
    cubin = ctypes.create_string_buffer(cubin_size.value)
    nvrtc.nvrtcGetCUBIN(program, cubin)
    nvrtc.nvrtcDestroyProgram(ctypes.byref(program))
    return cubin.raw[: cubin_size.value]


def load_kernel(name: str, source: str, entry: bytes) -> tuple[ctypes.CDLL, ctypes.c_void_p]:
    """Return the driver and a loaded function. The cubin file survives the process."""
    major, minor = torch.cuda.get_device_capability()
    arch = f"sm_{major}{minor}"
    digest = hashlib.sha256(f"{arch}\n{source}".encode("utf-8")).hexdigest()[:16]
    key = (name, entry, digest)
    cached = _LOADED.get(key)
    if cached is not None:
        return cached
    path = _CACHE / f"{name}_{arch}_{digest}.cubin"
    if path.exists() and path.stat().st_size > 0:
        image = path.read_bytes()
    else:
        image = _compile(source, arch)
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_suffix(".cubin.partial")
        partial.write_bytes(image)
        partial.replace(path)
    nvcuda = _nvcuda()
    torch.empty(1, device="cuda")
    module = ctypes.c_void_p()
    buffer = ctypes.create_string_buffer(image)
    loaded = nvcuda.cuModuleLoadData(ctypes.byref(module), buffer)
    if loaded != 0:
        raise RuntimeError(f"cuModuleLoadData failed: {loaded}")
    function = ctypes.c_void_p()
    found = nvcuda.cuModuleGetFunction(ctypes.byref(function), module, entry)
    if found != 0:
        raise RuntimeError(f"cuModuleGetFunction failed: {found}")
    _LOADED[key] = (nvcuda, function)
    return nvcuda, function
