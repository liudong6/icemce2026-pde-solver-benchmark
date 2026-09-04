from __future__ import annotations

import csv
from pathlib import Path
from typing import Sequence

from pdescale.benchmark import benchmark_rhs, estimate_sparse_memory_mb
from pdescale.coefficients import coefficient_metrics
from pdescale.conditioning import estimate_conditioning
from pdescale.grid import Grid2D
from pdescale.operators import assemble_operator
from pdescale.solvers import solve_system

AVERAGING_SENSITIVITY_FIELDS: tuple[str, ...] = (
    "coefficient_case",
    "family",
    "n",
    "n_unknowns",
    "face_average",
    "condition_n",
    "condition_estimate",
    "method",
    "tolerance",
    "converged",
    "iterations",
    "setup_seconds",
    "solve_seconds",
    "total_seconds",
    "residual_norm",
    "memory_estimate_mb",
    "best_method",
    "is_best",
    "speedup_vs_cg",
)


def _mark_best_solver(rows: list[dict[str, object]]) -> None:
    converged = [row for row in rows if bool(row["converged"])]
    best_method = ""
    cg_total = None
    if converged:
        best = min(converged, key=lambda row: float(row["total_seconds"]))
        best_method = str(best["method"])
        for row in converged:
            if row["method"] == "cg":
                cg_total = float(row["total_seconds"])
                break

    for row in rows:
        total = float(row["total_seconds"])
        row["best_method"] = best_method
        row["is_best"] = bool(best_method and row["method"] == best_method)
        row["speedup_vs_cg"] = (
            float(cg_total / total)
            if cg_total is not None and bool(row["converged"]) and total > 0.0
            else 0.0
        )


def run_averaging_sensitivity(
    *,
    coefficient_cases: Sequence[str],
    sizes: Sequence[int],
    face_averages: Sequence[str] = ("arithmetic", "harmonic"),
    methods: Sequence[str] = ("cg", "jacobi-pcg", "amg-pcg"),
    tolerance: float = 1e-8,
    maxiter: int = 12000,
    rhs: str = "ones",
    max_condition_n: int = 128,
    condition_tol: float = 1e-6,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    condition_cache: dict[tuple[str, str, int], float] = {}

    for coefficient_case in coefficient_cases:
        for n in sizes:
            grid = Grid2D(int(n), int(n))
            metrics = coefficient_metrics(grid, str(coefficient_case))
            b = benchmark_rhs(grid, str(coefficient_case), rhs)
            for face_average in face_averages:
                condition_n = min(int(n), int(max_condition_n))
                condition_key = (str(coefficient_case), str(face_average), condition_n)
                if condition_key not in condition_cache:
                    condition_cache[condition_key] = float(
                        estimate_conditioning(
                            Grid2D(condition_n, condition_n),
                            str(coefficient_case),
                            tol=condition_tol,
                            face_average=str(face_average),
                        )["condition_estimate"]
                    )

                A = assemble_operator(grid, str(coefficient_case), face_average=str(face_average))
                memory_estimate_mb = estimate_sparse_memory_mb(A)
                case_rows: list[dict[str, object]] = []
                for method in methods:
                    result = solve_system(
                        A,
                        b,
                        method=str(method),
                        tol=tolerance,
                        maxiter=maxiter,
                    )
                    case_rows.append(
                        {
                            "coefficient_case": str(coefficient_case),
                            "family": metrics["family"],
                            "n": int(n),
                            "n_unknowns": int(grid.num_interior),
                            "face_average": str(face_average),
                            "condition_n": int(condition_n),
                            "condition_estimate": float(condition_cache[condition_key]),
                            "method": result.method,
                            "tolerance": float(tolerance),
                            "converged": bool(result.converged),
                            "iterations": int(result.iterations),
                            "setup_seconds": float(result.setup_seconds),
                            "solve_seconds": float(result.solve_seconds),
                            "total_seconds": float(result.setup_seconds + result.solve_seconds),
                            "residual_norm": float(result.residual_norm),
                            "memory_estimate_mb": float(memory_estimate_mb),
                            "best_method": "",
                            "is_best": False,
                            "speedup_vs_cg": 0.0,
                        }
                    )
                _mark_best_solver(case_rows)
                rows.extend(case_rows)
    return rows


def write_averaging_sensitivity_csv(rows: Sequence[dict[str, object]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=AVERAGING_SENSITIVITY_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in AVERAGING_SENSITIVITY_FIELDS})
