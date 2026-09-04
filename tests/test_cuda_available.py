def test_capture_metadata_has_required_keys():
    from pdescale.metadata import capture_metadata

    meta = capture_metadata()
    for key in ["python", "platform", "cpu", "cpu_details", "memory_gb", "packages"]:
        assert key in meta


def test_capture_metadata_records_cpu_details():
    from pdescale.metadata import capture_metadata

    meta = capture_metadata()
    cpu_details = meta["cpu_details"]
    assert isinstance(cpu_details["name"], str)
    assert cpu_details["name"]
    assert cpu_details["logical_processors"] is None or cpu_details["logical_processors"] >= 1


def test_capture_metadata_records_cuda_status():
    from pdescale.metadata import capture_metadata

    meta = capture_metadata()
    assert "cuda" in meta
    assert "available" in meta["cuda"]


def test_write_metadata_json_persists_environment(tmp_path):
    import json
    from pdescale.metadata import write_metadata_json

    path = tmp_path / "environment.json"
    written = write_metadata_json(path)

    assert path.exists()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["cpu"] == written["cpu"]
    assert "numpy" in loaded["packages"]


def test_cuda_available_for_optional_experiment():
    from numba import cuda

    assert cuda.is_available()
