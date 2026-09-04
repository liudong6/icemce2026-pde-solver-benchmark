from __future__ import annotations

import argparse
from pathlib import Path

from pdescale.convergence import (
    estimate_order,
    load_convergence_case,
    run_convergence_case,
    write_convergence_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run manufactured-solution convergence experiments.")
    parser.add_argument(
        "--cases",
        nargs="+",
        default=[
            "experiments/cases/smooth_constant.yaml",
            "experiments/cases/smooth_variable.yaml",
        ],
    )
    parser.add_argument("--output", default="results/raw/convergence.csv")
    args = parser.parse_args()

    all_rows = []
    for case_path in args.cases:
        case = load_convergence_case(case_path)
        rows = run_convergence_case(case)
        order = estimate_order(
            [float(row["h"]) for row in rows],
            [float(row["l2_error"]) for row in rows],
        )
        print(f"{case.name}: L2 order={order:.3f}")
        for row in rows:
            status = "OK" if row["converged"] else "FAIL"
            print(
                f"  n={row['n']:4d} residual={row['residual_norm']:.3e} "
                f"L2={row['l2_error']:.3e} Linf={row['linf_error']:.3e} {status}"
            )
        all_rows.extend(rows)

    write_convergence_csv(all_rows, Path(args.output))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()

