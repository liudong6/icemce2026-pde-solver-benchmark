from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from pdescale.benchmark import benchmark_rhs, estimate_sparse_memory_mb
from pdescale.coefficients import coefficient_metrics
from pdescale.grid import Grid2D
from pdescale.operators import assemble_operator
from pdescale.solvers import solve_system


SOLVER_DECISION_FIELDS: tuple[str, ...] = (
    "coefficient_case",
    "family",
    "contrast_target",
    "contrast_observed",
    "grad_logk_inf",
    "total_variation_proxy",
    "n",
    "n_unknowns",
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


@dataclass(frozen=True)
class SolverDecisionStudy:
    coefficient_cases: Sequence[str]
    sizes: Sequence[int]
    methods: Sequence[str] = ("cg", "jacobi-pcg", "amg-pcg")
    tolerance: float = 1e-8
    maxiter: int = 20000
    rhs: str = "ones"

    def __post_init__(self) -> None:
        if not self.coefficient_cases:
            raise ValueError("at least one coefficient case is required")
        if not self.sizes:
            raise ValueError("at least one grid size is required")
        if any(int(n) < 4 for n in self.sizes):
            raise ValueError("grid sizes must be at least 4")
        if not self.methods:
            raise ValueError("at least one method is required")
        if self.tolerance <= 0.0:
            raise ValueError("tolerance must be positive")
        if self.maxiter <= 0:
            raise ValueError("maxiter must be positive")
        if self.rhs not in {"ones", "manufactured"}:
            raise ValueError("rhs must be 'ones' or 'manufactured'")


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


def run_solver_decision_study(study: SolverDecisionStudy) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for coefficient_case in study.coefficient_cases:
        for n in study.sizes:
            grid = Grid2D(int(n), int(n))
            metrics = coefficient_metrics(grid, coefficient_case)
            A = assemble_operator(grid, coefficient_case)
            b = benchmark_rhs(grid, coefficient_case, study.rhs)
            memory_estimate_mb = estimate_sparse_memory_mb(A)
            case_rows: list[dict[str, object]] = []

            for method in study.methods:
                result = solve_system(
                    A,
                    b,
                    method=str(method),
                    tol=study.tolerance,
                    maxiter=study.maxiter,
                )
                case_rows.append(
                    {
                        "coefficient_case": str(coefficient_case),
                        "family": metrics["family"],
                        "contrast_target": float(metrics["contrast_target"]),
                        "contrast_observed": float(metrics["contrast_observed"]),
                        "grad_logk_inf": float(metrics["grad_logk_inf"]),
                        "total_variation_proxy": float(metrics["total_variation_proxy"]),
                        "n": int(n),
                        "n_unknowns": int(grid.num_interior),
                        "method": result.method,
                        "tolerance": float(study.tolerance),
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
            output.extend(case_rows)
    return output


def write_solver_decision_csv(rows: Sequence[dict[str, object]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SOLVER_DECISION_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in SOLVER_DECISION_FIELDS})
