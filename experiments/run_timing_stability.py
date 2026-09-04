from __future__ import annotations

import argparse

from pdescale.decision import SolverDecisionStudy, run_solver_decision_study
from pdescale.timing_stability import (
    summarize_timing_repeats,
    write_timing_repeats_csv,
    write_timing_stability_csv,
)


DEFAULT_CASES = (
    "constant",
    "smooth_c30",
    "inclusion_c100",
    "layered_c100",
    "checkerboard_c100",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run repeated solver-decision timing checks.")
    parser.add_argument("--repeats-output", default="results/raw/timing_repeats.csv")
    parser.add_argument("--summary-output", default="results/raw/timing_stability.csv")
    parser.add_argument("--cases", nargs="+", default=list(DEFAULT_CASES))
    parser.add_argument("--sizes", nargs="+", type=int, default=[64, 128, 256])
    parser.add_argument("--methods", nargs="+", default=["cg", "jacobi-pcg", "amg-pcg"])
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--tolerance", type=float, default=1e-8)
    parser.add_argument("--maxiter", type=int, default=12000)
    args = parser.parse_args()

    if args.repeats < 2:
        raise ValueError("at least two repeats are required for timing stability")

    all_rows: list[dict[str, object]] = []
    for repeat_index in range(1, args.repeats + 1):
        study = SolverDecisionStudy(
            coefficient_cases=tuple(args.cases),
            sizes=tuple(args.sizes),
            methods=tuple(args.methods),
            tolerance=args.tolerance,
            maxiter=args.maxiter,
        )
        rows = run_solver_decision_study(study)
        for row in rows:
            row_with_repeat = {"repeat_index": repeat_index, **row}
            all_rows.append(row_with_repeat)
        print(f"completed repeat {repeat_index}/{args.repeats}")

    write_timing_repeats_csv(all_rows, args.repeats_output)
    summary_rows = summarize_timing_repeats(all_rows)
    write_timing_stability_csv(summary_rows, args.summary_output)
    print(f"wrote {args.repeats_output} ({len(all_rows)} rows)")
    print(f"wrote {args.summary_output} ({len(summary_rows)} rows)")


if __name__ == "__main__":
    main()
