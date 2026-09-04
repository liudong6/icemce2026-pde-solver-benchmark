import csv


def _sample_gpu_rows():
    return [
        {
            "n": 64,
            "n_unknowns": 1000,
            "method": "numba-parallel-cpu",
            "seconds_per_step": 0.0012,
        },
        {
            "n": 64,
            "n_unknowns": 1000,
            "method": "cuda-kernel",
            "seconds_per_step": 0.0018,
        },
        {
            "n": 128,
            "n_unknowns": 4000,
            "method": "numba-parallel-cpu",
            "seconds_per_step": 0.0042,
        },
        {
            "n": 128,
            "n_unknowns": 4000,
            "method": "cuda-kernel",
            "seconds_per_step": 0.0030,
        },
        {
            "n": 256,
            "n_unknowns": 16000,
            "method": "numba-parallel-cpu",
            "seconds_per_step": 0.0162,
        },
        {
            "n": 256,
            "n_unknowns": 16000,
            "method": "cuda-kernel",
            "seconds_per_step": 0.0070,
        },
    ]


def test_hardware_crossover_model_fits_cpu_and_cuda_rows():
    from pdescale.crossover import HARDWARE_CROSSOVER_FIELDS, fit_hardware_crossover

    rows = fit_hardware_crossover(_sample_gpu_rows())

    assert tuple(rows[0].keys()) == HARDWARE_CROSSOVER_FIELDS
    summary = next(row for row in rows if row["model_component"] == "crossover")
    assert summary["crossover_n_unknowns"] > 0.0
    assert summary["crossover_grid_n"] > 0.0
    assert summary["cpu_beta_seconds_per_unknown"] > summary["gpu_beta_seconds_per_unknown"]


def test_write_hardware_crossover_csv_uses_schema(tmp_path):
    from pdescale.crossover import (
        HARDWARE_CROSSOVER_FIELDS,
        fit_hardware_crossover,
        write_hardware_crossover_csv,
    )

    rows = fit_hardware_crossover(_sample_gpu_rows())
    output = tmp_path / "hardware_crossover_model.csv"
    write_hardware_crossover_csv(rows, output)

    with output.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        loaded = list(reader)
    assert tuple(reader.fieldnames) == HARDWARE_CROSSOVER_FIELDS
    assert {row["model_component"] for row in loaded} == {"cpu", "cuda", "crossover"}
