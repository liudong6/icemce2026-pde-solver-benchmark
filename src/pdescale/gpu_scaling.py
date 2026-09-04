from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Sequence

import numpy as np
from numba import cuda

from pdescale.cuda_kernels import (
    cuda_jacobi_steps,
    jacobi_bytes_per_step,
    launch_cuda_jacobi_steps,
    numba_jacobi_steps,
    numba_jacobi_steps_workspace,
)


GPU_STENCIL_FIELDS: tuple[str, ...] = (
    "n",
    "n_unknowns",
    "steps",
    "method",
    "repeats",
    "seconds_per_step",
    "steps_per_second",
    "estimated_gbytes_per_second",
    "max_abs_error",
    "speedup_vs_cpu",
)


@dataclass(frozen=True)
class GPUStencilCase:
    sizes: Sequence[int]
    steps: int = 20
    repeats: int = 3
    warmup: int = 1
    min_seconds: float = 0.2
    cpu_threads: int = 4
    block: tuple[int, int] = (16, 16)

    def __post_init__(self) -> None:
        if not self.sizes:
            raise ValueError("at least one grid size is required")
        if any(int(n) < 4 for n in self.sizes):
            raise ValueError("grid sizes must be at least 4")
        if self.steps < 1:
            raise ValueError("steps must be positive")
        if self.repeats < 1:
            raise ValueError("repeats must be positive")
        if self.warmup < 0:
            raise ValueError("warmup must be non-negative")
        if self.min_seconds < 0.0:
            raise ValueError("min_seconds must be non-negative")
        if self.cpu_threads < 1:
            raise ValueError("cpu_threads must be positive")
        if self.block[0] < 1 or self.block[1] < 1:
            raise ValueError("CUDA block dimensions must be positive")


def make_gpu_stencil_input(n: int) -> np.ndarray:
    x = np.linspace(0.0, 1.0, int(n), dtype=np.float64)
    y = np.linspace(0.0, 1.0, int(n), dtype=np.float64)
    xx, yy = np.meshgrid(x, y, indexing="ij")
    u = np.sin(np.pi * xx) * np.sin(2.0 * np.pi * yy)
    u[0, :] = 0.0
    u[-1, :] = 0.0
    u[:, 0] = 0.0
    u[:, -1] = 0.0
    return np.ascontiguousarray(u)


def _elapsed_to_row_values(elapsed: float, repeats: int, steps: int, bytes_per_step: int) -> tuple[float, float, float]:
    seconds_per_step = float(elapsed / (repeats * steps))
    steps_per_second = float(1.0 / seconds_per_step)
    bandwidth = float(bytes_per_step * steps_per_second / 1.0e9)
    return seconds_per_step, steps_per_second, bandwidth


def _time_cpu_jacobi_kernel(u0: np.ndarray, case: GPUStencilCase) -> tuple[float, int]:
    import numba

    numba.set_num_threads(case.cpu_threads)
    current = u0.copy()
    work = np.empty_like(current)
    for _ in range(case.warmup):
        current, work = numba_jacobi_steps_workspace(current, work, case.steps)

    calls = 0
    elapsed = 0.0
    start = perf_counter()
    while calls < case.repeats or elapsed < case.min_seconds:
        current, work = numba_jacobi_steps_workspace(current, work, case.steps)
        calls += 1
        elapsed = perf_counter() - start
    return float(elapsed), int(calls)


def _time_cuda_jacobi_kernel(u0: np.ndarray, case: GPUStencilCase) -> tuple[float, int]:
    d_current = cuda.to_device(u0)
    d_work = cuda.device_array_like(d_current)
    for _ in range(case.warmup):
        d_current, d_work = launch_cuda_jacobi_steps(
            d_current,
            d_work,
            case.steps,
            block=case.block,
            sync=True,
        )

    calls = 0
    elapsed = 0.0
    start = perf_counter()
    while calls < case.repeats or elapsed < case.min_seconds:
        d_current, d_work = launch_cuda_jacobi_steps(
            d_current,
            d_work,
            case.steps,
            block=case.block,
            sync=True,
        )
        calls += 1
        elapsed = perf_counter() - start
    return float(elapsed), int(calls)


def run_gpu_stencil_case(case: GPUStencilCase) -> list[dict[str, object]]:
    if not cuda.is_available():
        raise RuntimeError("CUDA is not available")

    rows: list[dict[str, object]] = []
    for n in case.sizes:
        u0 = make_gpu_stencil_input(int(n))
        n_unknowns = (int(n) - 2) ** 2
        bytes_per_step = jacobi_bytes_per_step(u0.shape)

        cpu_expected = numba_jacobi_steps(u0, case.steps)
        gpu_actual = cuda_jacobi_steps(u0, case.steps)
        max_abs_error = float(np.max(np.abs(gpu_actual - cpu_expected)))

        cpu_elapsed, cpu_repeats = _time_cpu_jacobi_kernel(u0, case)
        cpu_s_step, cpu_sps, cpu_bw = _elapsed_to_row_values(
            cpu_elapsed,
            cpu_repeats,
            case.steps,
            bytes_per_step,
        )
        gpu_elapsed, gpu_repeats = _time_cuda_jacobi_kernel(u0, case)
        gpu_s_step, gpu_sps, gpu_bw = _elapsed_to_row_values(
            gpu_elapsed,
            gpu_repeats,
            case.steps,
            bytes_per_step,
        )
        speedup = float(cpu_s_step / gpu_s_step)

        rows.append(
            {
                "n": int(n),
                "n_unknowns": int(n_unknowns),
                "steps": int(case.steps),
                "method": "numba-parallel-cpu",
                "repeats": int(cpu_repeats),
                "seconds_per_step": cpu_s_step,
                "steps_per_second": cpu_sps,
                "estimated_gbytes_per_second": cpu_bw,
                "max_abs_error": 0.0,
                "speedup_vs_cpu": 1.0,
            }
        )
        rows.append(
            {
                "n": int(n),
                "n_unknowns": int(n_unknowns),
                "steps": int(case.steps),
                "method": "cuda-kernel",
                "repeats": int(gpu_repeats),
                "seconds_per_step": gpu_s_step,
                "steps_per_second": gpu_sps,
                "estimated_gbytes_per_second": gpu_bw,
                "max_abs_error": max_abs_error,
                "speedup_vs_cpu": speedup,
            }
        )
    return rows


def decide_gpu_inclusion(
    rows: Sequence[dict[str, object]],
    *,
    min_n: int = 2048,
    min_speedup: float = 2.0,
) -> dict[str, object]:
    candidates = [
        row
        for row in rows
        if str(row["method"]) == "cuda-kernel"
        and int(row["n"]) >= min_n
        and float(row["max_abs_error"]) < 1e-9
    ]
    if not candidates:
        return {
            "include_in_main_paper": False,
            "max_speedup": 0.0,
            "n_at_max": None,
            "reason": f"no valid CUDA row for n >= {min_n}",
        }

    best = max(candidates, key=lambda row: float(row["speedup_vs_cpu"]))
    max_speedup = float(best["speedup_vs_cpu"])
    include = max_speedup > min_speedup
    reason = (
        f"CUDA kernel-only speedup {max_speedup:.2f}x at n={best['n']}"
        if include
        else f"maximum CUDA kernel-only speedup {max_speedup:.2f}x is below {min_speedup:.2f}x"
    )
    return {
        "include_in_main_paper": bool(include),
        "max_speedup": max_speedup,
        "n_at_max": int(best["n"]),
        "reason": reason,
    }


def write_gpu_stencil_csv(rows: Sequence[dict[str, object]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=GPU_STENCIL_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in GPU_STENCIL_FIELDS})


def load_gpu_stencil_case(path: str | Path) -> GPUStencilCase:
    import yaml

    with Path(path).open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    block = data.get("block", [16, 16])
    return GPUStencilCase(
        sizes=tuple(int(n) for n in data["sizes"]),
        steps=int(data.get("steps", 20)),
        repeats=int(data.get("repeats", 3)),
        warmup=int(data.get("warmup", 1)),
        min_seconds=float(data.get("min_seconds", 0.2)),
        cpu_threads=int(data.get("cpu_threads", 4)),
        block=(int(block[0]), int(block[1])),
    )
