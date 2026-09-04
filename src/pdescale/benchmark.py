from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
from scipy.sparse import issparse

from pdescale.grid import Grid2D
from pdescale.operators import assemble_operator
from pdescale.problems import rhs_manufactured
from pdescale.solvers import solve_system


SOLVER_BENCHMARK_FIELDS: tuple[str, ...] = (
    "case",
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
)


@dataclass(frozen=True)
class SolverBenchmarkCase:
    name: str
    coefficient_case: str
    sizes: Sequence[int]
    methods: Sequence[str]
    tolerance: float = 1e-8
    maxiter: int = 20000
    rhs: str = "ones"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("case name must be non-empty")
        if not self.sizes:
            raise ValueError("at least one grid size is required")
        if any(int(n) < 4 for n in self.sizes):
            raise ValueError("grid sizes must be at least 4")
        if not self.methods:
            raise ValueError("at least one solver method is required")
        if self.tolerance <= 0:
            raise ValueError("tolerance must be positive")
        if self.maxiter <= 0:
            raise ValueError("maxiter must be positive")
        if self.rhs not in {"ones", "manufactured"}:
            raise ValueError("rhs must be 'ones' or 'manufactured'")


def estimate_sparse_memory_mb(A: object, vector_count: int = 3) -> float:
    if not issparse(A):
        return 0.0
    matrix_bytes = A.data.nbytes + A.indices.nbytes + A.indptr.nbytes
    vector_bytes = vector_count * A.shape[0] * np.dtype(float).itemsize
    return float((matrix_bytes + vector_bytes) / 1024.0**2)


def benchmark_rhs(grid: Grid2D, coefficient_case: str, kind: str) -> np.ndarray:
    if kind == "ones":
        return np.ones(grid.num_interior, dtype=float)
    if kind == "manufactured":
        return rhs_manufactured(grid, coefficient_case)
    raise ValueError(f"unknown rhs kind: {kind}")


def run_solver_benchmark_case(case: SolverBenchmarkCase) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for n in case.sizes:
        grid = Grid2D(int(n), int(n))
        A = assemble_operator(grid, case.coefficient_case)
        b = benchmark_rhs(grid, case.coefficient_case, case.rhs)
        memory_estimate_mb = estimate_sparse_memory_mb(A)

        for method in case.methods:
            result = solve_system(
                A,
                b,
                method=method,
                tol=case.tolerance,
                maxiter=case.maxiter,
            )
            total_seconds = float(result.setup_seconds + result.solve_seconds)
            rows.append(
                {
                    "case": case.name,
                    "n": int(n),
                    "n_unknowns": int(grid.num_interior),
                    "method": result.method,
                    "tolerance": float(case.tolerance),
                    "converged": bool(result.converged),
                    "iterations": int(result.iterations),
                    "setup_seconds": float(result.setup_seconds),
                    "solve_seconds": float(result.solve_seconds),
                    "total_seconds": total_seconds,
                    "residual_norm": float(result.residual_norm),
                    "memory_estimate_mb": memory_estimate_mb,
                }
            )
    return rows


def write_solver_benchmark_csv(rows: Sequence[dict[str, object]], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SOLVER_BENCHMARK_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in SOLVER_BENCHMARK_FIELDS})


def load_solver_benchmark_case(path: str | Path) -> SolverBenchmarkCase:
    import yaml

    with Path(path).open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return SolverBenchmarkCase(
        name=str(data["name"]),
        coefficient_case=str(data["coefficient_case"]),
        sizes=tuple(int(n) for n in data["sizes"]),
        methods=tuple(str(method) for method in data["methods"]),
        tolerance=float(data.get("tolerance", 1e-8)),
        maxiter=int(data.get("maxiter", 20000)),
        rhs=str(data.get("rhs", "ones")),
    )
