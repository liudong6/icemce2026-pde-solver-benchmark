# Supplementary Artefact README

This package supports the ICEMCE 2026 manuscript:

`A Coefficient-Aware Finite-Difference Benchmark for Solver Selection and CPU/GPU Stencil Scaling in Heat-Conduction Simulation`

## Contents

- `src/pdescale/`: finite-difference operator, face-averaging checks, coefficient-field descriptors, conditioning estimates, descriptor-to-solver analysis, solver decision logic, timing-stability summaries, manufactured-solution problems, solvers, CPU scaling kernels, CUDA stencil kernels, plotting, and metadata utilities.
- `experiments/`: command-line entry points for convergence, solver comparison, coefficient-aware solver decision maps, conditioning estimates, discontinuous-interface verification, arithmetic/harmonic sensitivity analysis, descriptor-to-solver rank analysis, repeated solver timing, CPU scaling, CUDA scaling, hardware crossover fitting, table generation, and figure regeneration.
- `experiments/cases/`: YAML experiment configurations.
- `tests/`: pytest checks for operators, manufactured solutions, solvers, kernels, scaling summaries, and plotting.
- `results/raw/`: raw CSV files and environment metadata used to support reported results.
- `results/figures/`: generated figures.
- `paper/tables/`: manuscript table sources.
- `requirements.txt` and `requirements-cuda.txt`: CPU and CUDA Python dependencies.

## Reproduction Commands

Virtual environments are not distributed with this package. Run from the package root after creating one and installing the locked dependencies:

```powershell
py -3.12 -m venv .venv-cuda
.\.venv-cuda\Scripts\python.exe -m pip install --upgrade pip
.\.venv-cuda\Scripts\python.exe -m pip install -r requirements-cuda.txt
.\.venv-cuda\Scripts\python.exe -m pip install -e .
```

For a CPU-only check, install `requirements.txt` instead of `requirements-cuda.txt` and skip `run_gpu_stencil.py`.

The conditioning script includes `N=128` spectral estimates and took under one minute on the author machine; the face-averaging sensitivity script took about two minutes, and the repeated timing script uses five repeats for representative solver decisions and took about two minutes. For a quick smoke check, regenerate tables and figures from the included raw CSV files first, then rerun the conditioning, interface, sensitivity, and timing scripts when validating the full evidence chain.

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

If CUDA is unavailable, the CPU convergence, solver, and CPU scaling experiments remain reproducible; the CUDA crossover rows require an NVIDIA GPU and a working Numba-CUDA stack.

## Evidence Map

- `results/raw/convergence.csv`: manufactured-solution convergence rates and residuals.
- `results/raw/solver_benchmark.csv`: CG, Jacobi-PCG, and AMG-PCG iteration counts, residuals, setup time, solve time, total time, and memory estimate.
- `results/raw/solver_decision_map.csv`: coefficient-family decision grid with fastest converged solver labels.
- `results/raw/conditioning.csv`: spectral condition-number estimates for `N=32`, `N=64`, and `N=128`.
- `results/raw/interface_verification.csv`: one-dimensional two-material jump-interface verification for arithmetic and harmonic face averaging.
- `results/raw/difficulty_relationships.csv`: Spearman rank correlations linking coefficient descriptors to solver behaviour, including pooled all-grid rows, fixed-`N` strata, raw stratum coefficients, deterministic fixed-grid case-resampling intervals, and diagnostic 4999-permutation p-values. Condition numbers are matched to `N=64` and `N=128` where available; the `N=128` estimate is used as the maximum-available proxy for `N=256`.
- `results/raw/averaging_sensitivity.csv`: arithmetic/harmonic face-averaging sensitivity for discontinuous `C_k=100` stress cases.
- `results/raw/timing_repeats.csv`: raw repeated timing rows for representative solver-decision cases.
- `results/raw/timing_stability.csv`: median-best solver, vote fraction, speedup, and relative-IQR summary for repeated timings.
- `results/raw/cpu_scaling.csv`: NumPy, Numba serial, and Numba parallel stencil timings and estimated bandwidth.
- `results/raw/gpu_stencil.csv`: CPU and CUDA Jacobi kernel timings, estimated bandwidth, numerical agreement, and kernel-only speedup.
- `results/raw/hardware_crossover_model.csv`: empirical linear CPU/CUDA kernel crossover fit over the measured range.
- `results/raw/environment.json`: Python, package, CPU, memory, platform, and CUDA metadata.
- `paper/tables/*.tex`: manuscript tables regenerated from the raw CSV files.
- `cold_start_smoke_log.txt`: clean-extraction smoke-check log for table and figure regeneration from the packaged artefact.

## Stencil-Bandwidth Convention

The variable-coefficient stencil bandwidth estimate uses 11 double-precision values per interior point, or 88 bytes per point. The Jacobi crossover estimate uses five double-precision values per interior point, or 40 bytes per point. These are operational byte models for within-paper comparison, not hardware peak-bandwidth measurements.

## Scope Limits

The artefact does not claim industrial geometry support, unstructured finite elements, end-to-end GPU sparse-solver acceleration, general GPU superiority at all grid sizes, or a universal single coefficient-difficulty predictor.

No public repository DOI is claimed in the manuscript until a GitHub or Zenodo release is actually created.
