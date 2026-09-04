import csv
import math


def test_gpu_stencil_benchmark_records_speedup_decision():
    from pdescale.gpu_scaling import (
        GPU_STENCIL_FIELDS,
        GPUStencilCase,
        decide_gpu_inclusion,
        run_gpu_stencil_case,
    )

    case = GPUStencilCase(sizes=(256,), steps=4, repeats=1, warmup=1, min_seconds=0.0)
    rows = run_gpu_stencil_case(case)

    assert len(rows) == 2
    assert tuple(rows[0].keys()) == GPU_STENCIL_FIELDS
    assert {row["method"] for row in rows} == {"numba-parallel-cpu", "cuda-kernel"}
    for row in rows:
        assert row["n"] == 256
        assert row["n_unknowns"] == 254 * 254
        assert row["seconds_per_step"] > 0.0
        assert row["estimated_gbytes_per_second"] > 0.0
        assert math.isfinite(row["max_abs_error"])

    decision = decide_gpu_inclusion(rows, min_n=256, min_speedup=0.0)
    assert decision["include_in_main_paper"] is True


def test_write_gpu_stencil_csv_uses_schema(tmp_path):
    from pdescale.gpu_scaling import (
        GPU_STENCIL_FIELDS,
        GPUStencilCase,
        run_gpu_stencil_case,
        write_gpu_stencil_csv,
    )

    rows = run_gpu_stencil_case(GPUStencilCase(sizes=(256,), steps=2, repeats=1, warmup=0))
    csv_path = tmp_path / "gpu_stencil.csv"
    write_gpu_stencil_csv(rows, csv_path)

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        loaded = list(reader)
    assert tuple(reader.fieldnames) == GPU_STENCIL_FIELDS
    assert len(loaded) == 2
