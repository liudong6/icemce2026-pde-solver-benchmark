from __future__ import annotations

import argparse

from pdescale.decision import SolverDecisionStudy, run_solver_decision_study, write_solver_decision_csv


DEFAULT_CASES = (
    "constant",
    "smooth_c3",
    "smooth_c10",
    "smooth_c30",
    "inclusion_c10",
    "inclusion_c30",
    "inclusion_c100",
    "layered_c10",
    "layered_c30",
    "layered_c100",
    "checkerboard_c10",
    "checkerboard_c30",
    "checkerboard_c100",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run coefficient-aware solver decision-map experiments.")
    parser.add_argument("--output", default="results/raw/solver_decision_map.csv")
    parser.add_argument("--cases", nargs="+", default=list(DEFAULT_CASES))
    parser.add_argument("--sizes", nargs="+", type=int, default=[64, 128, 256])
    parser.add_argument("--methods", nargs="+", default=["cg", "jacobi-pcg", "amg-pcg"])
    parser.add_argument("--tolerance", type=float, default=1e-8)
    parser.add_argument("--maxiter", type=int, default=12000)
    args = parser.parse_args()

    study = SolverDecisionStudy(
        coefficient_cases=tuple(args.cases),
        sizes=tuple(args.sizes),
        methods=tuple(args.methods),
        tolerance=args.tolerance,
        maxiter=args.maxiter,
    )
    rows = run_solver_decision_study(study)
    write_solver_decision_csv(rows, args.output)
    print(f"wrote {args.output} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
