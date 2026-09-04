# ICEMCE 2026 PDE Solver Benchmark

This repository contains the reproducible code and experiments for an ICEMCE 2026 paper on variable-coefficient heat-conduction solvers and performance scaling.

Archived release:

- GitHub release: https://github.com/liudong6/icemce2026-pde-solver-benchmark/releases/tag/v1.0-icemce2026-submission

## Manuscript

Primary conference manuscript:

- `paper/icemce2026_iop_manuscript.docx`

Review/render copy:

- `paper/icemce2026_iop_manuscript.pdf`

Do not submit the LaTeX backup unless the conference explicitly asks for LaTeX source.

## Environment

Virtual environments are not distributed with the artefact. Create one after unpacking the package, then install the locked dependencies and the local package:

```powershell
py -3.12 -m venv .venv-cuda
.\.venv-cuda\Scripts\python.exe -m pip install --upgrade pip
.\.venv-cuda\Scripts\python.exe -m pip install -r requirements-cuda.txt
.\.venv-cuda\Scripts\python.exe -m pip install -e .
```

For a CPU-only check, use `requirements.txt` instead of `requirements-cuda.txt`. The core paper path is CPU-first with NumPy, SciPy, Numba, and PyAMG. CUDA experiments are optional and are used only when they pass the reproducibility gates. Confirm the environment with:

```powershell
.\.venv-cuda\Scripts\python.exe -m pytest -q
```

The conditioning script now includes `N=128` spectral estimates and took under one minute on the author machine; the face-averaging sensitivity script took about two minutes, and the repeated timing script uses five repeats for representative solver decisions and took about two minutes. For a quick smoke check, regenerate tables and figures from the included raw CSV files first, then rerun the conditioning, interface, sensitivity, and timing scripts when validating the full evidence chain.

## Reproducing the Reported Results

```powershell
.\.venv-cuda\Scripts\python.exe -m pytest -q
.\.venv-cuda\Scripts\python.exe experiments\run_convergence.py
.\.venv-cuda\Scripts\python.exe experiments\run_solvers.py
.\.venv-cuda\Scripts\python.exe experiments\run_decision_map.py
.\.venv-cuda\Scripts\python.exe experiments\run_conditioning.py
.\.venv-cuda\Scripts\python.exe experiments\run_interface_verification.py
.\.venv-cuda\Scripts\python.exe experiments\analyze_difficulty_relationships.py
.\.venv-cuda\Scripts\python.exe experiments\run_averaging_sensitivity.py
.\.venv-cuda\Scripts\python.exe experiments\run_timing_stability.py
.\.venv-cuda\Scripts\python.exe experiments\run_scaling.py
.\.venv-cuda\Scripts\python.exe experiments\run_gpu_stencil.py
.\.venv-cuda\Scripts\python.exe experiments\fit_hardware_crossover.py
.\.venv-cuda\Scripts\python.exe -m pdescale.metadata --output results\raw\environment.json
.\.venv-cuda\Scripts\python.exe experiments\make_paper_tables.py
.\.venv-cuda\Scripts\python.exe experiments\make_all_figures.py --only all
```

Raw evidence tables and environment metadata are under `results/raw/`, including `solver_decision_map.csv`, `conditioning.csv`, `interface_verification.csv`, `difficulty_relationships.csv`, `averaging_sensitivity.csv`, `timing_repeats.csv`, `timing_stability.csv`, and `hardware_crossover_model.csv`. The difficulty-relationship CSV reports both pooled all-grid correlations and fixed-`N` strata, with raw stratum coefficients, deterministic fixed-grid case-resampling intervals, and diagnostic 4999-permutation p-values. Condition numbers are matched to `N=64` and `N=128` where available; the `N=128` estimate is used as the maximum-available proxy for `N=256`. Manuscript tables are regenerated under `paper/tables/`. Figures are generated under `results/figures/` and copied into `paper/figures/` by `make_all_figures.py`. The file `cold_start_smoke_log.txt` records a clean-extraction smoke check of the packaged artefact.

The current supplementary upload package is generated as `submission/supplementary_artefact.zip`.
