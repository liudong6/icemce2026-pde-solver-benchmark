import csv


def test_harmonic_interface_verification_is_more_accurate_than_arithmetic():
    from pdescale.interface_verification import solve_layer_interface

    arithmetic = solve_layer_interface(64, face_average="arithmetic")
    harmonic = solve_layer_interface(64, face_average="harmonic")

    assert harmonic["l2_error"] < arithmetic["l2_error"]
    assert harmonic["flux_error_abs"] < arithmetic["flux_error_abs"]


def test_write_interface_verification_csv_uses_schema(tmp_path):
    from pdescale.interface_verification import (
        INTERFACE_VERIFICATION_FIELDS,
        run_interface_verification,
        write_interface_verification_csv,
    )

    rows = run_interface_verification(sizes=(16,), face_averages=("arithmetic", "harmonic"))
    output = tmp_path / "interface_verification.csv"
    write_interface_verification_csv(rows, output)

    with output.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        loaded = list(reader)
    assert tuple(reader.fieldnames) == INTERFACE_VERIFICATION_FIELDS
    assert len(loaded) == 2
