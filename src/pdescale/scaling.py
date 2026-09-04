from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Callable, Sequence

import numpy as np

from pdescale.grid import Grid2D
from pdescale.numba_kernels import (
    numba_apply_stencil,
    numba_apply_stencil_serial,
    numpy_apply_stencil,
    stencil_bytes_per_apply,
)
from pdescale.problems import k_field


CPU_SCALING_FIELDS: tuple[str, ...] = (
    "n",
    "n_unknowns",
    "coefficient_case",
    "method",
    "threads",
    "repeats",
    "seconds_per_apply",
    "applies_per_second",
    "estimated_gbytes_per_second",
    "max_abs_error",
)


@dataclass(frozen=True)
class CPUScalingCase:
    sizes: Sequence[int]
    coefficient_case: str = "smooth"
    methods: Sequence[str] = ("numpy-vectorized", "numba-serial", "numba-parallel")
    threads: Sequence[int] = (1, 2, 4, 8, 16)
    repeats: int = 5
    warmup: int = 2
    min_seconds: float = 0.0

    def __post_init__(self) -> None:
        if not self.sizes:
            raise ValueError("at least one grid size is required")
        if any(int(n) < 4 for n in self.sizes):
            raise ValueError("grid sizes must be at least 4")
        if not self.methods:
            raise ValueError("at least one method is required")
        if any(int(t) < 1 for t in self.threads):
            raise ValueError("thread counts must be positive")
        if self.repeats < 1:
            raise ValueError("repeats must be positive")
        if self.warmup < 0:
            raise ValueError("warmup must be non-negative")
        if self.min_seconds < 0.0:
            raise ValueError("min_seconds must be non-negative")


def available_numba_threads() -> int:
    import numba

    return int(numba.config.NUMBA_DEFAULT_NUM_THREADS)


def make_stencil_inputs(n: int, coefficient_case: str) -> tuple[Grid2D, np.ndarray, np.ndarray]:
    grid = Grid2D(int(n), int(n))
    u = np.sin(np.pi * grid.x) * np.sin(2.0 * np.pi * grid.y)
    k = k_field(grid.x, grid.y, coefficient_case)
    return grid, np.ascontiguousarray(u), np.ascontiguousarray(k)


def _method_function(method: str) -> Callable[[np.ndarray, np.ndarray, np.ndarray, float, float], None]:
    if method == "numpy-vectorized":
        return numpy_apply_stencil
    if method == "numba-serial":
        return numba_apply_stencil_serial
    if method == "numba-parallel":
        return numba_apply_stencil
    raise ValueError(f"unknown scaling method: {method}")


def _thread_values_for_method(method: str, threads: Sequence[int]) -> tuple[int, ...]:
    if method in {"numpy-vectorized", "numba-serial"}:
        return (1,)
    max_threads = available_numba_threads()
    return tuple(t for t in (int(value) for value in threads) if t <= max_threads)


def _time_stencil(
    apply: Callable[[np.ndarray, np.ndarray, np.ndarray, float, float], None],
    u: np.ndarray,
    k: np.ndarray,
    out: np.ndarray,
    hx: float,
    hy: float,
    *,
    warmup: int,
    repeats: int,
    min_seconds: float,
) -> tuple[float, int]:
    for _ in range(warmup):
        apply(u, k, out, hx, hy)
    start = perf_counter()
    calls = 0
    elapsed = 0.0
    while calls < repeats or elapsed < min_seconds:
        apply(u, k, out, hx, hy)
        calls += 1
        elapsed = perf_counter() - start
    return float(elapsed / calls), calls


def run_cpu_scaling_case(case: CPUScalingCase) -> list[dict[str, object]]:
    import numba

    rows: list[dict[str, object]] = []
    for n in case.sizes:
        grid, u, k = make_stencil_inputs(int(n), case.coefficient_case)
        reference = np.zeros_like(u)
        numpy_apply_stencil(u, k, reference, grid.hx, grid.hy)
        bytes_per_apply = stencil_bytes_per_apply(u.shape)

        for method_value in case.methods:
            method = str(method_value)
            apply = _method_function(method)
            for threads in _thread_values_for_method(method, case.threads):
                if method == "numba-parallel":
                    numba.set_num_threads(int(threads))
                out = np.zeros_like(u)
                seconds_per_apply, actual_repeats = _time_stencil(
                    apply,
                    u,
                    k,
                    out,
                    grid.hx,
                    grid.hy,
                    warmup=case.warmup,
                    repeats=case.repeats,
                    min_seconds=case.min_seconds,
                )
                max_abs_error = float(np.max(np.abs(out - reference)))
                applies_per_second = 1.0 / seconds_per_apply
                rows.append(
                    {
                        "n": int(n),
                        "n_unknowns": int(grid.num_interior),
                        "coefficient_case": case.coefficient_case,
                        "method": method,
                        "threads": int(threads),
                        "repeats": int(actual_repeats),
                        "seconds_per_apply": seconds_per_apply,
                        "applies_per_second": applies_per_second,
                        "estimated_gbytes_per_second": float(
                            bytes_per_apply * applies_per_second / 1.0e9
                        ),
                        "max_abs_error": max_abs_error,
                    }
                )
    return rows


def write_cpu_scaling_csv(rows: Sequence[dict[str, object]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CPU_SCALING_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in CPU_SCALING_FIELDS})
