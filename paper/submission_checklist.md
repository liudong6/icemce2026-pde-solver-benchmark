# ICEMCE 2026 Submission Checklist

## Second-round review revision — v5 / v1.2

This complete revision is identified by Zenodo v5, https://doi.org/10.5281/zenodo.22874266, and GitHub release https://github.com/liudong6/icemce2026-pde-solver-benchmark/releases/tag/v1.2-icemce2026-review-revision. The v4 DOI identifies the earlier baseline and controlled extension. This revision adds 378 paired callback-calibration solves, the complete nine-cell face-averaging table in the main paper, an explicit interface-resistance interpretation, and distinct scopes for historical, extension and calibration timings. Original raw files are unchanged. The primary Word/PDF manuscript highlights review changes in yellow.

Reproduce the new tables without rerunning timings:

```powershell
python experiments/analyze_protocol_sensitivity.py
```

The prospective design is `experiments/protocol_sensitivity.md`; raw timings, configuration, source hashes and environment are in `results/raw/protocol_sensitivity`. Method quartiles, paired ratios, winner votes and the numerical audit are in `results/analysis/protocol_sensitivity`. To rerun measurements, use `python experiments/run_protocol_sensitivity.py --output results/raw/protocol_sensitivity_rerun` in an unused directory, with no other performance workload running. Existing evidence is never overwritten.

All 378 recorded residuals are at most 1e-8, and all 189 mode pairs have identical solution hashes and iteration counts. Median solve-time inflation is 1.54–1.84 for CG, 1.58–1.77 for Jacobi, and 1.03–1.06 for AMG. The nine median winners agree between callbacks, but vote instability is retained. These results do not reconstruct historical cold-import/thread/order effects or establish a machine-independent crossover.


## Manuscript Status

- [x] LaTeX manuscript source: `paper/main.tex`
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

- [x] Do not claim setup-inclusive diffusion benchmarking is new; compare directly with HPGMG-FV and AMG2023.
- [x] Do not describe the retrospective fastest-solver labels as a validated predictive or online selector.
- [x] Report all 15 available repeated-timing case-size cells, including the constant-grid near tie.
- [x] Do not attribute constant-coefficient CG/Jacobi timing differences to improved conditioning.
- [x] Keep the unvalidated four-point crossover fit in supplementary materials and report no fitted hardware threshold.

- [x] Do not claim industrial-scale validation.
- [x] Do not claim end-to-end GPU solver acceleration.
- [x] Do not claim unstructured FEM capability.
- [x] Do not claim general superiority of GPU for all grid sizes.
- [x] Do not claim `G_k^{(h)}` is a universal or fixed-grid strongest predictor.
- [x] Do not claim fixed-`N` descriptor rankings are significantly separated when case-resampling intervals overlap.
- [x] Do not describe the solver decision map as a repeated-right-hand-side or setup-amortised model.
- [x] Do not treat selected-solver speedup correlations as primary solver-difficulty evidence; iteration-count associations are the primary diagnostic.
- [x] Do not present harmonic averaging as a universal discretisation for curved or non-grid-aligned material interfaces.
- [x] Do not use the exploratory `N≈755` fit intersection as a hardware-selection threshold; the CPU fit predicts a negative time at the measured `N=512` point.
- [x] Separate the historical monitored protocol from the new warm-import, shuffled-order, count-only protocol; do not pool their timing conclusions.
- [x] Distinguish the older baseline DOI, published v4 extension DOI, and the presently unpublished callback calibration.
- [x] Preserve published v4 DOI 10.5281/zenodo.22668106 as the identity of the earlier extension. The 20 September calibration is assigned v5 DOI 10.5281/zenodo.22874266.
- [ ] Publish a new GitHub/Zenodo version for this local 20 September revision and retain its receipt. The prior v4 release is unchanged.
- [x] On 9 September 2026, inspect the conference-linked submission platform at https://www.ais.cn/attendees/index/FYEY3M: it announces a third-round full-paper deadline of 18 September 2026 at 23:59, IOP Journal of Physics: Conference Series publication, and a single-column manuscript of at least six full pages. This newer platform notice differs from the English homepage's 15 August deadline.
- [ ] Complete the authenticated submission workflow and retain its receipt; the public paper-submission link currently requests login, so inspection of the announcement does not prove that a manuscript has been received or accepted.
- [x] Disclose the recorded AI models and actual uses, including experiment design, code implementation, numerical analysis and manuscript preparation; state the author's confirmed independent review and responsibility for the final content.

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

## Controlled extension review

- [x] Preserve the 13 baseline raw files and distinguish their version DOI from the new data.
- [x] Verify exact descriptor matches, flux-energy identities and reflection/transpose controls.
- [x] Retain all 576 pilot solves, including failed acceptance checks.
- [x] Verify all 2212 geometry/forcing follow-up solves and 744 portfolio-audit solves against the independent true-residual threshold.
- [x] Report the interleaved three-method confirmation: 17/24 stable cells, 3/12 stable translated-pair reversals, and portfolio-conditional cost floors.
- [x] Report complete case summaries and unstable winners, not only the illustrated reversal.
- [x] Distinguish established invariant-subspace/island theory from this specific benchmark audit.
- [x] On 8 September 2026, the author confirmed independent review of the matched-field, source-perturbation and classical-AMG experiments and the ability to explain their key derivations, timing boundaries and failure cases. This records the author's confirmation, separately from automated verification.

- [x] Verify a newly installed CPU-only environment: 91 passed, 5 explicit CUDA skips; 76 regenerated/recorded outputs match byte-for-byte.
- [x] Require CUDA explicitly for GPU validation: the existing CUDA environment passes all 96 tests; a CPU-only environment rejects this mode.

## Revision verification, 20 September 2026

- [x] 378 calibration rows accepted; 189 paired solution hashes and iteration counts identical.
- [x] All 35 original raw CSV/JSON files retain their pre-revision SHA-256.
- [x] Clean-extraction verification: 96 tests passed with CUDA required; all regenerated/retained outputs byte-identical.
- [x] Word-exported PDF visually inspected: 15 pages, nine data tables, six figures and 27 references. LaTeX has no undefined references or overfull boxes.
