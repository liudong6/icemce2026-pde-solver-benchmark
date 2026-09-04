from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

import numpy as np
from scipy.sparse import issparse
from scipy.sparse.linalg import LinearOperator, cg, spsolve


@dataclass(frozen=True)
class SolveResult:
    solution: np.ndarray
    converged: bool
    iterations: int
    residual_norm: float
    setup_seconds: float
    solve_seconds: float
    method: str
    residual_history: list[float] = field(default_factory=list)
    error: str | None = None


def _canonical_method(method: str) -> str:
    key = method.strip().lower().replace("_", "-")
    aliases = {
        "direct": "direct",
        "spsolve": "direct",
        "cg": "cg",
        "jacobi": "jacobi-pcg",
        "jacobi-pcg": "jacobi-pcg",
        "pcg-jacobi": "jacobi-pcg",
        "amg": "amg-pcg",
        "amg-pcg": "amg-pcg",
        "pcg-amg": "amg-pcg",
    }
    if key not in aliases:
        raise ValueError(f"unknown solver method: {method}")
    return aliases[key]


def _matvec(A_or_op: Any, x: np.ndarray) -> np.ndarray:
    return np.asarray(A_or_op @ x)


def _relative_residual(A_or_op: Any, b: np.ndarray, x: np.ndarray) -> float:
    residual = _matvec(A_or_op, x) - b
    denominator = max(float(np.linalg.norm(b)), np.finfo(float).tiny)
    return float(np.linalg.norm(residual) / denominator)


def _failure_result(
    *,
    method: str,
    b: np.ndarray,
    setup_seconds: float,
    solve_seconds: float,
    error: Exception | str,
    residual_history: list[float] | None = None,
) -> SolveResult:
    message = error if isinstance(error, str) else f"{type(error).__name__}: {error}"
    return SolveResult(
        solution=np.full_like(b, np.nan, dtype=float),
        converged=False,
        iterations=0 if residual_history is None else len(residual_history),
        residual_norm=float("inf"),
        setup_seconds=setup_seconds,
        solve_seconds=solve_seconds,
        method=method,
        residual_history=[] if residual_history is None else residual_history,
        error=str(message),
    )


def _jacobi_preconditioner(A_or_op: Any) -> LinearOperator:
    if not hasattr(A_or_op, "diagonal"):
        raise TypeError("Jacobi preconditioning requires an assembled matrix with diagonal()")
    diagonal = np.asarray(A_or_op.diagonal(), dtype=float)
    if np.any(diagonal == 0.0):
        raise ZeroDivisionError("Jacobi preconditioner encountered a zero diagonal entry")
    inverse_diagonal = 1.0 / diagonal
    return LinearOperator(
        shape=A_or_op.shape,
        matvec=lambda x: inverse_diagonal * x,
        dtype=float,
    )


def _amg_preconditioner(A_or_op: Any) -> LinearOperator:
    if not issparse(A_or_op):
        raise TypeError("AMG preconditioning requires an assembled sparse matrix")
    import pyamg

    ml = pyamg.smoothed_aggregation_solver(A_or_op)
    return ml.aspreconditioner(cycle="V")


def _run_cg(
    A_or_op: Any,
    b: np.ndarray,
    *,
    method: str,
    tol: float,
    maxiter: int,
    preconditioner: LinearOperator | None,
    setup_seconds: float,
) -> SolveResult:
    residual_history: list[float] = []

    def callback(xk: np.ndarray) -> None:
        residual_history.append(_relative_residual(A_or_op, b, xk))

    solve_start = perf_counter()
    try:
        solution, info = cg(
            A_or_op,
            b,
            rtol=tol,
            atol=0.0,
            maxiter=maxiter,
            M=preconditioner,
            callback=callback,
        )
        solve_seconds = perf_counter() - solve_start
    except Exception as exc:
        solve_seconds = perf_counter() - solve_start
        return _failure_result(
            method=method,
            b=b,
            setup_seconds=setup_seconds,
            solve_seconds=solve_seconds,
            error=exc,
            residual_history=residual_history,
        )

    residual_norm = _relative_residual(A_or_op, b, solution)
    converged = bool(info == 0 and residual_norm <= max(tol * 10.0, tol + 1e-14))
    return SolveResult(
        solution=np.asarray(solution),
        converged=converged,
        iterations=len(residual_history),
        residual_norm=residual_norm,
        setup_seconds=setup_seconds,
        solve_seconds=solve_seconds,
        method=method,
        residual_history=residual_history,
        error=None if converged else f"cg returned info={info}",
    )


def solve_system(
    A_or_op: Any,
    b: np.ndarray,
    method: str,
    tol: float,
    maxiter: int,
    grid: Any = None,
    case: str | None = None,
) -> SolveResult:
    del grid, case
    canonical = _canonical_method(method)
    rhs = np.asarray(b, dtype=float)

    if canonical == "direct":
        setup_start = perf_counter()
        setup_seconds = perf_counter() - setup_start
        solve_start = perf_counter()
        try:
            solution = np.asarray(spsolve(A_or_op, rhs), dtype=float)
            solve_seconds = perf_counter() - solve_start
        except Exception as exc:
            solve_seconds = perf_counter() - solve_start
            return _failure_result(
                method=canonical,
                b=rhs,
                setup_seconds=setup_seconds,
                solve_seconds=solve_seconds,
                error=exc,
            )
        residual_norm = _relative_residual(A_or_op, rhs, solution)
        return SolveResult(
            solution=solution,
            converged=residual_norm <= max(tol * 10.0, tol + 1e-14),
            iterations=0,
            residual_norm=residual_norm,
            setup_seconds=setup_seconds,
            solve_seconds=solve_seconds,
            method=canonical,
            residual_history=[],
            error=None,
        )

    setup_start = perf_counter()
    preconditioner: LinearOperator | None = None
    try:
        if canonical == "jacobi-pcg":
            preconditioner = _jacobi_preconditioner(A_or_op)
        elif canonical == "amg-pcg":
            preconditioner = _amg_preconditioner(A_or_op)
    except Exception as exc:
        setup_seconds = perf_counter() - setup_start
        return _failure_result(
            method=canonical,
            b=rhs,
            setup_seconds=setup_seconds,
            solve_seconds=0.0,
            error=exc,
        )
    setup_seconds = perf_counter() - setup_start

    return _run_cg(
        A_or_op,
        rhs,
        method=canonical,
        tol=tol,
        maxiter=maxiter,
        preconditioner=preconditioner,
        setup_seconds=setup_seconds,
    )

