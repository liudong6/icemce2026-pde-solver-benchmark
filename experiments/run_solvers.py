from __future__ import annotations

import argparse
from pathlib import Path

from pdescale.benchmark import (
    load_solver_benchmark_case,
    run_solver_benchmark_case,
    write_solver_benchmark_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run sparse PDE solver benchmark experiments.")
    parser.add_argument(
        "--cases",
        nargs="+",
        default=[
            "experiments/cases/solver_smooth.yaml",
            "experiments/cases/high_contrast.yaml",
        ],
    )
    parser.add_argument("--output", default="results/raw/solver_benchmark.csv")
    args = parser.parse_args()

    all_rows = []
    for case_path in args.cases:
        case = load_solver_benchmark_case(case_path)
        rows = run_solver_benchmark_case(case)
        print(f"{case.name}:")
        for row in rows:
            status = "OK" if row["converged"] else "FAIL"
            print(
                f"  n={row['n']:4d} method={row['method']:<10s} "
                f"iters={row['iterations']:5d} total={row['total_seconds']:.3f}s "
                f"residual={row['residual_norm']:.3e} {status}"
            )
        all_rows.extend(rows)

    write_solver_benchmark_csv(all_rows, Path(args.output))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
