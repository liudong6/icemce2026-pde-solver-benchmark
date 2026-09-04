import csv


def test_cpu_scaling_case_records_accuracy_and_throughput():
    from pdescale.scaling import (
        CPU_SCALING_FIELDS,
        CPUScalingCase,
        run_cpu_scaling_case,
    )

    case = CPUScalingCase(
        sizes=(16,),
        coefficient_case="smooth",
        methods=("numpy-vectorized", "numba-parallel"),
        threads=(1, 2),
        repeats=1,
        warmup=1,
    )
    rows = run_cpu_scaling_case(case)

    assert len(rows) == 3
    assert tuple(rows[0].keys()) == CPU_SCALING_FIELDS
    for row in rows:
        assert row["n"] == 16
        assert row["n_unknowns"] == 14 * 14
        assert row["seconds_per_apply"] > 0.0
        assert row["applies_per_second"] > 0.0
        assert row["estimated_gbytes_per_second"] > 0.0
        assert row["max_abs_error"] < 1e-8


def test_write_cpu_scaling_csv_uses_schema(tmp_path):
    from pdescale.scaling import (
        CPU_SCALING_FIELDS,
        CPUScalingCase,
        run_cpu_scaling_case,
        write_cpu_scaling_csv,
    )

    case = CPUScalingCase(
        sizes=(12,),
        methods=("numpy-vectorized",),
        threads=(1,),
        repeats=1,
        warmup=0,
    )
    rows = run_cpu_scaling_case(case)
    csv_path = tmp_path / "cpu_scaling.csv"

    write_cpu_scaling_csv(rows, csv_path)

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        loaded = list(reader)
    assert tuple(reader.fieldnames) == CPU_SCALING_FIELDS
    assert len(loaded) == 1
    assert loaded[0]["method"] == "numpy-vectorized"


def test_cpu_scaling_records_actual_repeats_for_minimum_timing_window():
    from pdescale.scaling import CPUScalingCase, run_cpu_scaling_case

    case = CPUScalingCase(
        sizes=(12,),
        methods=("numpy-vectorized",),
        threads=(1,),
        repeats=1,
        warmup=0,
        min_seconds=0.001,
    )
    rows = run_cpu_scaling_case(case)

    assert rows[0]["repeats"] >= 1
