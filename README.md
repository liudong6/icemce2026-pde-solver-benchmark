# ICEMCE 2026 PDE Solver Benchmark

## Second-round review revision — v5 / v1.2

This complete revision is identified by Zenodo v5, https://doi.org/10.5281/zenodo.22874266, and GitHub release https://github.com/liudong6/icemce2026-pde-solver-benchmark/releases/tag/v1.2-icemce2026-review-revision. The v4 DOI identifies the earlier baseline and controlled extension. This revision adds 378 paired callback-calibration solves, the complete nine-cell face-averaging table in the main paper, an explicit interface-resistance interpretation, and distinct scopes for historical, extension and calibration timings. Original raw files are unchanged. The primary Word/PDF manuscript highlights review changes in yellow.

Reproduce the new tables without rerunning timings:

```powershell
python experiments/analyze_protocol_sensitivity.py
```

The prospective design is `experiments/protocol_sensitivity.md`; raw timings, configuration, source hashes and environment are in `results/raw/protocol_sensitivity`. Method quartiles, paired ratios, winner votes and the numerical audit are in `results/analysis/protocol_sensitivity`. To rerun measurements, use `python experiments/run_protocol_sensitivity.py --output results/raw/protocol_sensitivity_rerun` in an unused directory, with no other performance workload running. Existing evidence is never overwritten.

All 378 recorded residuals are at most 1e-8, and all 189 mode pairs have identical solution hashes and iteration counts. Median solve-time inflation is 1.54–1.84 for CG, 1.58–1.77 for Jacobi, and 1.03–1.06 for AMG. The nine median winners agree between callbacks, but vote instability is retained. These results do not reconstruct historical cold-import/thread/order effects or establish a machine-independent crossover.


This repository contains the reproducible code and experiments for an ICEMCE 2026 paper on variable-coefficient heat-conduction solvers and performance scaling.

Published benchmark-data baseline:

- GitHub release: https://github.com/liudong6/icemce2026-pde-solver-benchmark/releases/tag/v1.1-icemce2026-submission
- Zenodo archived version (v4): https://doi.org/10.5281/zenodo.22668106
- Baseline version: https://doi.org/10.5281/zenodo.22303525

The revision retains the baseline evidence and adds a controlled matched-field and forcing audit. New raw data are in `results/raw/counterfactual`; the release and version DOI above identify that previously published extension and its manuscript, before the local 20 September revision. `MANIFEST.sha256` records each packaged snapshot.

The extension uses exact matching of scalar coefficient descriptors, rigid translations, source and transpose controls, independent motifs, fresh-setup timings and preconditioned spectral diagnostics. The geometry/forcing follow-up comprises 2212 accepted solves; the candidate-solver audit adds 744, giving 2956 accepted extension solves in total; 576 exploratory pilot solves are also retained, including failures. It gives measured counterexamples to invariant-only solver choice, not a new Krylov/AMG algorithm or an online selector. The original decision map remains a separate monitored-implementation baseline.

Run `python experiments/analyze_counterfactual.py` and `python experiments/analyze_portfolio.py` to regenerate both extension stages from the recorded CSV files. See [controlled reproduction instructions](experiments/counterfactual/README.md) for the full sequential experiment commands and timing boundaries. The descriptive rank-correlation table and iteration-scaling plot remain in the supplementary outputs.

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

## Regenerating the recorded results

Use these commands for the initial numerical review. They read the archived
measurements and regenerate tables, figures and analyses without rerunning timings:

```powershell
python -m pytest -q -rs
python experiments/make_paper_tables.py
python experiments/make_all_figures.py --only all
python experiments/analyze_counterfactual.py
python experiments/analyze_portfolio.py
```

See `paper/EVIDENCE_MAP.md` for the source of each main result. Compare the
archive's SHA256 manifest before modifying the extracted files.

## Rerunning baseline measurements

Run the following only in a separate extraction reserved for new measurements.
The historical scripts write into `results/raw` and can replace the extracted
baseline CSVs and environment record. Keep the original archive and its first
extraction intact for comparison. New wall-clock times are new observations;
they should not silently replace the published measurements when interpreting
the manuscript. The controlled extension has separate non-overwriting commands
in `experiments/counterfactual/README.md`.


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

## Timing Interpretation

Historical baseline solver timings include a callback that recomputes the true relative residual at every iteration. This adds a sparse matrix-vector product and norm evaluations to each iteration. The solver rankings and speedups apply to this monitored implementation. Matrix assembly and right-hand-side construction are excluded; methods run in a fixed order, and the first AMG setup in a fresh process includes the PyAMG import.

The historical baseline scripts do not fix PyAMG spectral-estimation random starts, and historical BLAS thread settings and processor power states were not recorded. Numerical reruns and timing reruns therefore need not reproduce every hierarchy-dependent iteration count or wall-clock value exactly. Reported spectral condition estimates describe the unpreconditioned matrix; the `N=256` diagnostic uses the `N=128` proxy. Reproduction of tables and figures from the archived CSV files is deterministic in the tested environment.

The four-point CPU/CUDA linear fit is exploratory: its CPU curve predicts a negative time at the measured `N=512` point. The intersection near `N=755` is not a validated hardware-selection threshold. CUDA measurements cover resident-data batches, including Python launch and final synchronisation overhead, and exclude allocation, compilation warm-up, and transfers.

## Building the Manuscript

The numerical requirements do not include document tooling. Install `python-docx` separately to run `python tools/build_iop_docx.py`; the IOP template is included under `template/icemce2026/WordGuidelines/WordGuidelines/`. On Windows, `powershell -File tools/export_iop_pdf.ps1` exports the DOCX using the installed `Word.Application` COM provider (Microsoft Word or a compatible WPS installation). Inspect the exported PDF because pagination depends on the office renderer. The LaTeX backup requires a TeX distribution and can be built with `latexmk -pdf main.tex` from `paper/`.


The candidate-solver sensitivity extension adds 744 accepted solves, including a 504-solve interleaved confirmation with classical AMG. Rebuild its summaries with `python experiments/analyze_portfolio.py`. See `experiments/counterfactual/README.md` for settings, timing boundaries, portfolio-dependent cost floors, and safe rerun instructions. These data are included in the revised artefact at https://doi.org/10.5281/zenodo.22668106; the earlier baseline DOI identifies the retained baseline measurements only.


## CPU-only and required-CUDA test modes

After installing `requirements.txt`, run `python -m pytest -q -rs`. Tests that
require the optional CUDA runtime/device are explicitly skipped when CUDA is
unavailable; all CPU, numerical, data-analysis and metadata tests still run.
To validate a CUDA installation, run `python -m pytest -q --require-cuda`.
This mode fails when CUDA is unavailable, so a GPU validation run cannot pass
by silently skipping its GPU tests. The five CUDA-dependent tests carry the
`cuda` marker and can also be selected with `-m cuda --require-cuda`.

The optional `requirements-cpu-verified.txt` pins the resolved CPU dependency
set, including transitive dependencies, for Windows x86-64/Python3.12.
Install it instead of `requirements.txt` when reproducing that exact CPU
dependency set. Install the extracted project itself with `pip install -e .`.
Document export and CUDA use their separately described runtimes.

The fresh CPU environment check passed 91 tests with 5 explicit CUDA skips and reproduced 76 recorded/generated outputs byte-for-byte. The existing CUDA environment passed all 96 tests with `--require-cuda`. Dependency versions and the scope of this check are recorded in `results/raw/counterfactual/reproduction_environment.json`; the package smoke log records the commands.

`paper/EVIDENCE_MAP.md` maps main text results, tables and figures to recorded inputs and regeneration commands. The main manuscript presents all 12 interleaved translated pairs and explicitly defines the portfolio-conditional cost floor. Complete face-averaging and baseline timing-stability tables remain in `paper/tables/` as supplementary evidence.
