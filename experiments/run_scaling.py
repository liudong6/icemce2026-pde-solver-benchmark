from __future__ import annotations

import argparse
from pathlib import Path

from pdescale.scaling import CPUScalingCase, run_cpu_scaling_case, write_cpu_scaling_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CPU stencil performance scaling experiments.")
    parser.add_argument("--sizes", nargs="+", type=int, default=[256, 512, 1024, 2048])
    parser.add_argument("--threads", nargs="+", type=int, default=[1, 2, 4, 8, 16])
    parser.add_argument(
        "--methods",
        nargs="+",
        default=["numpy-vectorized", "numba-serial", "numba-parallel"],
    )
    parser.add_argument("--coefficient-case", default="smooth")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--min-seconds", type=float, default=0.2)
    parser.add_argument("--output", default="results/raw/cpu_scaling.csv")
    args = parser.parse_args()

    case = CPUScalingCase(
        sizes=tuple(args.sizes),
        coefficient_case=args.coefficient_case,
        methods=tuple(args.methods),
        threads=tuple(args.threads),
        repeats=args.repeats,
        warmup=args.warmup,
        min_seconds=args.min_seconds,
    )
    rows = run_cpu_scaling_case(case)
    for row in rows:
        print(
            f"n={row['n']:4d} method={row['method']:<16s} threads={row['threads']:2d} "
            f"time={row['seconds_per_apply']:.6f}s "
            f"bw={row['estimated_gbytes_per_second']:.2f} GB/s "
            f"err={row['max_abs_error']:.3e}"
        )
    write_cpu_scaling_csv(rows, Path(args.output))
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
