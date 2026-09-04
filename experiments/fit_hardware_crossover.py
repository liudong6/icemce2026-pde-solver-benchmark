from __future__ import annotations

import argparse

from pdescale.crossover import fit_hardware_crossover, read_gpu_rows, write_hardware_crossover_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Fit a linear CPU/CUDA stencil crossover model.")
    parser.add_argument("--gpu-stencil-csv", default="results/raw/gpu_stencil.csv")
    parser.add_argument("--output", default="results/raw/hardware_crossover_model.csv")
    args = parser.parse_args()

    rows = fit_hardware_crossover(read_gpu_rows(args.gpu_stencil_csv))
    write_hardware_crossover_csv(rows, args.output)
    print(f"wrote {args.output} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
