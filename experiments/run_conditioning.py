from __future__ import annotations

import argparse

from pdescale.conditioning import run_conditioning_study, write_conditioning_csv


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
    parser = argparse.ArgumentParser(description="Estimate spectral conditioning for coefficient families.")
    parser.add_argument("--output", default="results/raw/conditioning.csv")
    parser.add_argument("--cases", nargs="+", default=list(DEFAULT_CASES))
    parser.add_argument("--sizes", nargs="+", type=int, default=[32, 64, 128])
    parser.add_argument("--tol", type=float, default=1e-6)
    parser.add_argument("--face-average", choices=["arithmetic", "harmonic"], default="arithmetic")
    args = parser.parse_args()

    rows = run_conditioning_study(
        coefficient_cases=tuple(args.cases),
        sizes=tuple(args.sizes),
        tol=args.tol,
        face_average=args.face_average,
    )
    write_conditioning_csv(rows, args.output)
    print(f"wrote {args.output} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
