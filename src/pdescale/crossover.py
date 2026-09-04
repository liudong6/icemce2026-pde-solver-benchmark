from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Sequence

import numpy as np


HARDWARE_CROSSOVER_FIELDS: tuple[str, ...] = (
    "model_component",
    "method",
    "observations",
    "alpha_seconds",
    "beta_seconds_per_unknown",
    "r2",
    "crossover_n_unknowns",
    "crossover_grid_n",
    "cpu_alpha_seconds",
    "cpu_beta_seconds_per_unknown",
    "gpu_alpha_seconds",
    "gpu_beta_seconds_per_unknown",
)


def _fit_line(rows: Sequence[dict[str, object]], method: str) -> dict[str, float]:
    points = [
        (float(row["n_unknowns"]), float(row["seconds_per_step"]))
        for row in rows
        if str(row["method"]) == method
    ]
    if len(points) < 2:
        raise ValueError(f"at least two observations are required for {method}")
    x = np.asarray([point[0] for point in points], dtype=float)
    y = np.asarray([point[1] for point in points], dtype=float)
    beta, alpha = np.polyfit(x, y, deg=1)
    predicted = alpha + beta * x
    ss_res = float(np.sum((y - predicted) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 if ss_tot == 0.0 else 1.0 - ss_res / ss_tot
    return {
        "observations": float(len(points)),
        "alpha_seconds": float(alpha),
        "beta_seconds_per_unknown": float(beta),
        "r2": float(r2),
    }


def _crossover_unknowns(cpu: dict[str, float], gpu: dict[str, float]) -> float:
    denominator = cpu["beta_seconds_per_unknown"] - gpu["beta_seconds_per_unknown"]
    numerator = gpu["alpha_seconds"] - cpu["alpha_seconds"]
    if denominator <= 0.0:
        return float("nan")
    return float(numerator / denominator)


def fit_hardware_crossover(rows: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    cpu = _fit_line(rows, "numba-parallel-cpu")
    gpu = _fit_line(rows, "cuda-kernel")
    crossover_n = _crossover_unknowns(cpu, gpu)
    crossover_grid = float(math.sqrt(crossover_n) + 2.0) if crossover_n > 0.0 else float("nan")

    def row(component: str, method: str, model: dict[str, float]) -> dict[str, object]:
        return {
            "model_component": component,
            "method": method,
            "observations": int(model["observations"]),
            "alpha_seconds": model["alpha_seconds"],
            "beta_seconds_per_unknown": model["beta_seconds_per_unknown"],
            "r2": model["r2"],
            "crossover_n_unknowns": crossover_n if component == "crossover" else 0.0,
            "crossover_grid_n": crossover_grid if component == "crossover" else 0.0,
            "cpu_alpha_seconds": cpu["alpha_seconds"],
            "cpu_beta_seconds_per_unknown": cpu["beta_seconds_per_unknown"],
            "gpu_alpha_seconds": gpu["alpha_seconds"],
            "gpu_beta_seconds_per_unknown": gpu["beta_seconds_per_unknown"],
        }

    crossover = {
        "observations": min(cpu["observations"], gpu["observations"]),
        "alpha_seconds": 0.0,
        "beta_seconds_per_unknown": 0.0,
        "r2": min(cpu["r2"], gpu["r2"]),
    }
    return [
        row("cpu", "numba-parallel-cpu", cpu),
        row("cuda", "cuda-kernel", gpu),
        row("crossover", "linear_cpu_vs_cuda", crossover),
    ]


def read_gpu_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_hardware_crossover_csv(rows: Sequence[dict[str, object]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HARDWARE_CROSSOVER_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in HARDWARE_CROSSOVER_FIELDS})
