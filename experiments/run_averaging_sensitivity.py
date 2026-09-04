from __future__ import annotations

import argparse

from pdescale.averaging_sensitivity import run_averaging_sensitivity, write_averaging_sensitivity_csv


DEFAULT_CASES = (
    "inclusion_c100",
    "layered_c100",
    "checkerboard_c100",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare arithmetic and harmonic face averaging for discontinuous coefficient stress cases.")
    parser.add_argument("--output", default="results/raw/averaging_sensitivity.csv")
    parser.add_argument("--cases", nargs="+", default=list(DEFAULT_CASES))
    parser.add_argument("--sizes", nargs="+", type=int, default=[64, 128, 256])
    parser.add_argument("--face-averages", nargs="+", default=["arithmetic", "harmonic"])
    parser.add_argument("--methods", nargs="+", default=["cg", "jacobi-pcg", "amg-pcg"])
    parser.add_argument("--tolerance", type=float, default=1e-8)
    parser.add_argument("--maxiter", type=int, default=12000)
    parser.add_argument("--max-condition-n", type=int, default=128)
    args = parser.parse_args()

    rows = run_averaging_sensitivity(
        coefficient_cases=tuple(args.cases),
        sizes=tuple(args.sizes),
        face_averages=tuple(args.face_averages),
        methods=tuple(args.methods),
        tolerance=args.tolerance,
        maxiter=args.maxiter,
        max_condition_n=args.max_condition_n,
    )
    write_averaging_sensitivity_csv(rows, args.output)
    print(f"wrote {args.output} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
