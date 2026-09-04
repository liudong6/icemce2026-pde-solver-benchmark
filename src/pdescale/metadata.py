from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _memory_gb() -> float | None:
    try:
        import psutil

        return round(psutil.virtual_memory().total / 1024**3, 3)
    except Exception:
        return None


def _windows_cpu_name() -> str | None:
    if platform.system().lower() != "windows":
        return None
    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return None
    name = completed.stdout.strip()
    return name or None


def _cpu_metadata() -> dict[str, Any]:
    logical_processors = os.cpu_count()
    physical_cores: int | None = None
    max_frequency_mhz: float | None = None
    try:
        import psutil

        physical_cores = psutil.cpu_count(logical=False)
        freq = psutil.cpu_freq()
        if freq is not None and freq.max:
            max_frequency_mhz = round(float(freq.max), 3)
    except Exception:
        pass

    detected_name = (
        _windows_cpu_name()
        or platform.processor()
        or platform.uname().processor
        or platform.machine()
    )
    return {
        "name": detected_name,
        "machine": platform.machine(),
        "processor": platform.processor(),
        "physical_cores": physical_cores,
        "logical_processors": logical_processors,
        "max_frequency_mhz": max_frequency_mhz,
    }


def _cuda_metadata() -> dict[str, Any]:
    data: dict[str, Any] = {"available": False, "devices": []}
    try:
        from numba import cuda

        data["available"] = bool(cuda.is_available())
        if data["available"]:
            for index in range(len(cuda.gpus)):
                device = cuda.gpus[index]
                with device:
                    current = cuda.get_current_device()
                    name = current.name
                    if isinstance(name, bytes):
                        name = name.decode("utf-8", errors="replace")
                    data["devices"].append(
                        {
                            "id": index,
                            "name": name,
                            "compute_capability": current.compute_capability,
                        }
                    )
    except Exception as exc:
        data["error"] = f"{type(exc).__name__}: {exc}"
    return data


def capture_metadata() -> dict[str, Any]:
    packages = {
        name: _package_version(name)
        for name in [
            "numpy",
            "scipy",
            "numba",
            "pyamg",
            "numba-cuda",
            "matplotlib",
            "pytest",
            "psutil",
            "PyYAML",
        ]
    }
    cpu_details = _cpu_metadata()
    return {
        "python": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "cpu": cpu_details["name"],
        "cpu_details": cpu_details,
        "memory_gb": _memory_gb(),
        "packages": packages,
        "cuda": _cuda_metadata(),
    }


def write_metadata_json(path: str | Path) -> dict[str, Any]:
    metadata = capture_metadata()
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metadata


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Capture reproducibility environment metadata.")
    parser.add_argument(
        "--output",
        default="results/raw/environment.json",
        help="Path for the environment metadata JSON file.",
    )
    args = parser.parse_args()
    metadata = write_metadata_json(args.output)
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
