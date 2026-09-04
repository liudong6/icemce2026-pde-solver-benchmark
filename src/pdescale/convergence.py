from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from pdescale.grid import Grid2D
from pdescale.operators import assemble_operator, interior_to_vector
from pdescale.problems import rhs_manufactured, u_exact
from pdescale.solvers import solve_system


CONVERGENCE_FIELDS: tuple[str, ...] = (
    "case_name",
    "coefficient_case",
    "n",
    "n_unknowns",
    "h",
    "method",
    "tol",
    "maxiter",
    "converged",
    "iterations",
    "residual_norm",
    "solve_seconds",
    "l2_error",
    "linf_error",
)


@dataclass(frozen=True)
class ConvergenceCase:
    name: str
    coefficient_case: str
    sizes: Sequence[int]
    method: str = "cg"
    tol: float = 1e-11
    maxiter: int = 20000

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("case name must be non-empty")
        if len(self.sizes) < 3:
            raise ValueError("at least three grid sizes are required for convergence")
        if any(int(n) < 4 for n in self.sizes):
            raise ValueError("grid sizes must be at least 4")
        if self.tol <= 0:
            raise ValueError("tol must be positive")
        if self.maxiter <= 0:
            raise ValueError("maxiter must be positive")


def estimate_order(h_values: Iterable[float], errors: Iterable[float]) -> float:
    h = np.asarray(list(h_values), dtype=float)
    e = np.asarray(list(errors), dtype=float)
    if h.size != e.size:
        raise ValueError("h_values and errors must have the same length")
    if h.size < 2:
        raise ValueError("at least two points are required to estimate order")
    if np.any(h <= 0.0) or np.any(e <= 0.0):
        raise ValueError("h_values and errors must be positive")
    slope, _ = np.polyfit(np.log(h), np.log(e), deg=1)
    return float(slope)


def error_norms(numerical: np.ndarray, exact: np.ndarray) -> tuple[float, float]:
    diff = np.asarray(numerical, dtype=float) - np.asarray(exact, dtype=float)
    return float(np.sqrt(np.mean(diff**2))), float(np.max(np.abs(diff)))


def run_convergence_case(case: ConvergenceCase) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for n in case.sizes:
        grid = Grid2D(int(n), int(n))
        A = assemble_operator(grid, case.coefficient_case)
        b = rhs_manufactured(grid, case.coefficient_case)
        result = solve_system(
            A,
            b,
            method=case.method,
            tol=case.tol,
            maxiter=case.maxiter,
        )
        exact = interior_to_vector(u_exact(grid.x, grid.y))
        l2_error, linf_error = error_norms(result.solution, exact)
        rows.append(
            {
                "case_name": case.name,
                "coefficient_case": case.coefficient_case,
                "n": int(n),
                "n_unknowns": int(grid.num_interior),
                "h": float(grid.hx),
                "method": result.method,
                "tol": float(case.tol),
                "maxiter": int(case.maxiter),
                "converged": bool(result.converged),
                "iterations": int(result.iterations),
                "residual_norm": float(result.residual_norm),
                "solve_seconds": float(result.solve_seconds),
                "l2_error": l2_error,
                "linf_error": linf_error,
            }
        )
    return rows


def write_convergence_csv(rows: Sequence[dict[str, object]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CONVERGENCE_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in CONVERGENCE_FIELDS})


def load_convergence_case(path: str | Path) -> ConvergenceCase:
    import yaml

    with Path(path).open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return ConvergenceCase(
        name=str(data["name"]),
        coefficient_case=str(data["coefficient_case"]),
        sizes=tuple(int(n) for n in data["sizes"]),
        method=str(data.get("method", "cg")),
        tol=float(data.get("tol", 1e-11)),
        maxiter=int(data.get("maxiter", 20000)),
    )

