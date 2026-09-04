from __future__ import annotations

import argparse

from pdescale.interface_verification import run_interface_verification, write_interface_verification_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify arithmetic and harmonic interface averaging on a 1D layered analytic problem.")
    parser.add_argument("--output", default="results/raw/interface_verification.csv")
    parser.add_argument("--sizes", nargs="+", type=int, default=[32, 64, 128, 256])
    parser.add_argument("--face-averages", nargs="+", default=["arithmetic", "harmonic"])
    parser.add_argument("--k-left", type=float, default=1.0)
    parser.add_argument("--k-right", type=float, default=100.0)
    args = parser.parse_args()

    rows = run_interface_verification(
        sizes=tuple(args.sizes),
        face_averages=tuple(args.face_averages),
        k_left=args.k_left,
        k_right=args.k_right,
    )
    write_interface_verification_csv(rows, args.output)
    print(f"wrote {args.output} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
