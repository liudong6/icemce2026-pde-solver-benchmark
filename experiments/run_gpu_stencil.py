from __future__ import annotations

import argparse
from pathlib import Path

from pdescale.gpu_scaling import (
    decide_gpu_inclusion,
    load_gpu_stencil_case,
    run_gpu_stencil_case,
    write_gpu_stencil_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run optional CUDA Jacobi stencil crossover benchmark.")
    parser.add_argument("--case", default="experiments/cases/gpu_stencil.yaml")
    parser.add_argument("--output", default="results/raw/gpu_stencil.csv")
    args = parser.parse_args()

    case = load_gpu_stencil_case(args.case)
    rows = run_gpu_stencil_case(case)
    for row in rows:
        print(
            f"n={row['n']:4d} method={row['method']:<18s} "
            f"time/step={row['seconds_per_step']:.6e}s "
            f"bw={row['estimated_gbytes_per_second']:.2f} GB/s "
            f"speedup={row['speedup_vs_cpu']:.2f}x "
            f"err={row['max_abs_error']:.3e}"
        )

    decision = decide_gpu_inclusion(rows)
    print(
        "decision="
        f"{'include' if decision['include_in_main_paper'] else 'omit'}; "
        f"{decision['reason']}"
    )

    write_gpu_stencil_csv(rows, Path(args.output))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
