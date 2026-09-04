# ICEMCE 2026 Submission Checklist

## Manuscript Status

- [x] Full-paper skeleton created: `paper/main.tex`
- [x] Bibliography file created: `paper/references.bib`
- [x] Main figures copied to `paper/figures/`
- [x] Main tables created in `paper/tables/`
- [x] Results are tied to raw CSV files under `results/raw/`
- [x] Environment metadata is persisted as `results/raw/environment.json`
- [x] Python dependencies are locked in `requirements.txt` and `requirements-cuda.txt`
- [x] Author affiliation, postcode, country, and email completed in `paper/icemce2026_iop_manuscript.docx`
- [x] ICEMCE/IOP official Word template checked against final formatting requirements
- [x] Page length checked after template migration and methodology/timing additions
- [x] Primary submission file set: `paper/icemce2026_iop_manuscript.docx`
- [x] Secondary review PDF generated: `paper/icemce2026_iop_manuscript.pdf`
- [x] LaTeX backup regenerated as single-column A4 to avoid accidental two-column upload
- [x] Reference DOI/URL existence checked through DOI resolution and Crossref metadata lookup

## Evidence Chain

- [x] Discretisation verification: `results/raw/convergence.csv`
- [x] Solver/preconditioner benchmark: `results/raw/solver_benchmark.csv`
- [x] CPU stencil scaling: `results/raw/cpu_scaling.csv`
- [x] CUDA crossover benchmark: `results/raw/gpu_stencil.csv`
- [x] Coefficient-aware solver decision map: `results/raw/solver_decision_map.csv`
- [x] Spectral conditioning estimates: `results/raw/conditioning.csv`
- [x] Discontinuous-interface face-averaging verification: `results/raw/interface_verification.csv`
- [x] Descriptor-to-solver rank correlations, including pooled/fixed-`N` views, raw fixed-`N` stratum coefficients, fixed-grid case-resampling intervals, and diagnostic permutation p-values: `results/raw/difficulty_relationships.csv`
- [x] Arithmetic/harmonic sensitivity for discontinuous `C_k=100` stress cases: `results/raw/averaging_sensitivity.csv`
- [x] Repeated solver timing stability: `results/raw/timing_repeats.csv` and `results/raw/timing_stability.csv`
- [x] Hardware crossover model: `results/raw/hardware_crossover_model.csv`
- [x] Test suite: `python -m pytest -q`
- [x] Environment metadata: `results/raw/environment.json`
- [x] Manuscript tables regenerated from CSV: `experiments/make_paper_tables.py`
- [x] Headline manuscript claims recalculated from raw CSV and matched within stated tolerances
- [x] Supplementary ZIP cold-start extraction passed: pytest, table regeneration, and figure regeneration

## Main Claims Allowed

- [x] The finite-difference discretisation recovers second-order convergence on manufactured smooth tests.
- [x] AMG-PCG strongly reduces iterations and runtime on the high-contrast benchmark.
- [x] The single-pass setup-inclusive fastest solver changes with grid size: Jacobi-PCG is selected at the smallest tested grid; AMG-PCG dominates the larger tested grids.
- [x] The one-dimensional aligned jump-interface check shows harmonic face averaging recovers analytic flux to roundoff, while arithmetic averaging has grid-refined interface error.
- [x] The discontinuous `C_k=100` arithmetic/harmonic sensitivity check changes iterations and condition estimates but not the tested fastest-solver class.
- [x] Repeated timing supports the nonconstant `N=256` AMG-PCG selections and flags the constant-coefficient `N=64` case as a near-tie.
- [x] Coefficient geometry matters; stratified rank-correlation evidence with uncertainty checks shows that no single contrast or sharpness descriptor is a universal difficulty metric.
- [x] Numba improves repeated CPU stencil throughput over NumPy for this benchmark.
- [x] CUDA gives kernel-only speedup above 2x for `N >= 2048` when data stay resident on the device.
- [x] Estimated stencil bandwidth uses stated byte models: 88 B/interior point for the variable-coefficient stencil and 40 B/interior point for the Jacobi crossover.

## Claims Not Allowed

- [x] Do not claim industrial-scale validation.
- [x] Do not claim end-to-end GPU solver acceleration.
- [x] Do not claim unstructured FEM capability.
- [x] Do not claim general superiority of GPU for all grid sizes.
- [x] Do not claim `G_k^{(h)}` is a universal or fixed-grid strongest predictor.
- [x] Do not claim fixed-`N` descriptor rankings are significantly separated when case-resampling intervals overlap.
- [x] Do not describe the solver decision map as a repeated-right-hand-side or setup-amortised model.
- [x] Do not treat selected-solver speedup correlations as primary solver-difficulty evidence; iteration-count associations are the primary diagnostic.
- [x] Do not present harmonic averaging as a universal discretisation for curved or non-grid-aligned material interfaces.
- [x] Do not present the `N≈755` CPU/CUDA crossover as more than an illustrative interpolation over measured Jacobi-kernel timings.
- [x] Cite the public repository DOI only after confirming the GitHub release and Zenodo version actually contain the current submission artefact.
- [x] Include a narrow AI-assistance disclosure when required by the publisher or conference policy.

## Commands to Reproduce

```powershell
py -3.12 -m venv .venv-cuda
.\.venv-cuda\Scripts\python.exe -m pip install --upgrade pip
.\.venv-cuda\Scripts\python.exe -m pip install -r requirements-cuda.txt
.\.venv-cuda\Scripts\python.exe -m pip install -e .
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
