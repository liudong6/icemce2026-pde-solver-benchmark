# Manuscript evidence map — six-page revision

Main and supplementary numbers below identify the 3 October presentation. The scientific datasets are unchanged. Historical, controlled-extension and paired-calibration timings remain separate.

| Current location | Evidence | Regeneration |
|---|---|---|
| Main Table 1; Supplement Table S6 | `results/raw/averaging_sensitivity.csv` | `experiments/analyze_protocol_sensitivity.py` |
| Main Table 2; Supplement Table S7 | `results/raw/protocol_sensitivity/timings.csv` | Same analyser; all candidate quartiles, paired ratios and votes in `results/analysis/protocol_sensitivity` |
| Main Table 3; Supplement Table S8 | `results/raw/counterfactual/portfolio_confirmation.csv` | `experiments/analyze_portfolio.py` |
| Main Figure 1; original Supplement Figure S4 | `results/raw/counterfactual/confirmation.csv` | Compact: `tools/plot_compact_counterfactual.py`; original: `experiments/analyze_counterfactual.py`. Medians and full five-run ranges, no confidence-interval claim |
| Main Section 2; Supplement Tables S1–S2 / Figure S1 | `results/raw/convergence.csv`, `interface_verification.csv` | `experiments/make_paper_tables.py`, `experiments/make_all_figures.py` |
| Main Sections 2–3; Supplement Tables S3–S5 / Figures S2–S3 | `conditioning.csv`, `solver_decision_map.csv`, `solver_benchmark.csv` in `results/raw` | Same generators; preserve N128 spectral proxy for N256 |
| Main Section 5; Supplement Table S9 / Figures S5–S6 | `results/raw/cpu_scaling.csv`, `gpu_stencil.csv` | Same generators; variable-coefficient CPU apply and resident-data Jacobi CUDA are distinct experiments |

`tools/build_iop_docx.py` calls `tools/build_compact_manuscript.py` to build the Word main paper and synchronise LaTeX from `paper/compact_manuscript.txt` and `compact_references.json`. `tools/build_supplementary_methods.py` extracts complete methods/results from the retained pre-compression Word source, preserving tables, native equations and media. Full reference titles remain in that supplement, BibTeX and the audit. The current main retains 31 references, 18 recent and one preprint.

## Numerical statements in the text

In this list, `counterfactual/` abbreviates `results/raw/counterfactual/`.

- **Second-order convergence:** `convergence.csv`, columns `h`, `l2_error`,
  `linf_error`; rates are fitted across the recorded N32,64,128,256 grids.
- **Condition estimates 6.43e5 versus 3.12e4:** `conditioning.csv`, N128,
  `inclusion_c100` and `checkerboard_c100`, column `condition_estimate`.
  These describe the unpreconditioned matrix, not the preconditioned spectrum.
- **Pooled correlation 0.94:** `difficulty_relationships.csv`; use `descriptor=condition_estimate`,
  `response=selected_speedup_vs_cg`, and `n_group=all`. Fixed-N strata have 13 cases and overlapping
  case-resampling intervals. `experiments/analyze_difficulty_relationships.py`
  records the calculation. This is descriptive evidence from designed cases.
- **Baseline speedups 2.79, 7.80, 25.72:** `solver_decision_map.csv`; median at
  N64, median at N=256 and largest N256 selected-method speedup respectively.
- **4370/535/12 iterations and 6.155/0.288 seconds:** `solver_benchmark.csv`,
  high-contrast case at N=256, CG/Jacobi/AMG rows. These use the historical
  per-iteration residual-monitoring timer and must not be presented as the
  count-only extension's timings.
- **Original matched pair 403→677 iterations, 72.2/101.0 and 125.1/97.5 ms:**
  `counterfactual/confirmation.csv`, N192,c1000,disconnected,harmonic,
  `dipole_x`, centered/shift_x, Jacobi/SA0. Random forcing on the centered
  matrix gives 949 iterations and 166.2/94.3 ms. These are five-run medians.
- **1.142 ratio and 2 of 48 stable reversals:**
  `results/analysis/counterfactual/translation_floors_summary.csv`, rebuilt
  from the complete `confirmation.csv`. The illustrated ratio is restricted
  to the Jacobi/SA portfolio and gives each position weight 1/2.
- **Source perturbation 403→569 iterations:** `counterfactual/perturbation.csv`,
  N192, centered disconnected field, odd source plus constant admixture 1e-8;
  `experiments/counterfactual/perturbation.py` specifies normalization.
- **New N128 pair 266→450 iterations and 24.3/36.8 versus 42.3/34.2 ms:**
  `counterfactual/portfolio_confirmation.csv`, original 2x8 motif, odd_x,
  shifts 0 and 1, Jacobi/classical AMG. Median times are from this interleaved stage
  only. Classical AMG requires 11 iterations at both positions.
- **11.91% and zero N192 median floor:**
  `results/analysis/counterfactual/portfolio_translation_floors.csv`;
  recompute with `experiments/analyze_portfolio.py` and main Equation 3 / supplementary Equation S9. For every
  candidate, average its time divided by the per-position oracle time; take
  the smallest candidate average and subtract 1. The smallest median-based
  floor can be zero even when individual repeats have different winners.
- **CPU 0.1813, 0.005325, 0.003725 s/apply:** `cpu_scaling.csv`, N2048,
  NumPy, Numba serial, Numba parallel/four threads respectively.
- **CUDA 1.52, 3.23, 3.51 speedups:** `gpu_stencil.csv`, N1024,2048,4096,
  `cuda-kernel` rows and `speedup_vs_cpu`. These include launch and final
  synchronization and exclude allocation, compilation and transfers.

## Controls, denominators and retained supplementary tables

The original geometry/forcing follow-ups comprise 1440 confirmation,
640 independent-family and 132 perturbation solves. The portfolio stages add 240
screen and 504 interleaved confirmation solves. All 2956 pass the independently
checked true-relative-residual acceptance threshold 1e-8. The 576-solve pilot
uses a different threshold and retains 84 failures; it is not included in that
accepted-follow-up total.

Confirmation winner stability is 124/144 cells, independent-family stability
55/64, and interleaved portfolio stability 17/24. The corresponding translated
pair denominators are 48 for the original confirmation and 12 for the interleaved
portfolio confirmation; the latter uses an already studied 3x6 anchor and is
not an unseen-geometry test. Each config JSON identifies the actual workload,
seeds, repetitions and solver settings. Source hashes and routing changes are
recorded in the two source-provenance JSON files.

The face-averaging table remains in
`paper/tables/averaging_sensitivity_summary.tex`, with all 9 discontinuous
case-size comparisons in `results/raw/averaging_sensitivity.csv`. The full
15-cell timing-stability table remains in
`paper/tables/timing_stability_summary.tex`, backed by `timing_repeats.csv`
and `timing_stability.csv`. The near-tie constant N=64 result is retained.
The original rank-correlation table, iteration plot and invalid four-point
crossover-fit summary also remain in the supplementary artefact.

Offline spectral evidence is in `counterfactual/mechanism.csv`,
`spectrum_validation.json` and `spectral_validation_attempts.json`.
`portfolio_spd_checks.json` records the eight small-grid inverse-preconditioner
checks. These are numerical checks, not rigorous eigenvalue enclosures or a
general proof of solver robustness.

## Safe regeneration and interpretation

```powershell
python experiments/make_paper_tables.py
python experiments/make_all_figures.py --only all
python experiments/analyze_counterfactual.py
python experiments/analyze_portfolio.py
python -m pytest -q -rs
```

GPU validation requires `python -m pytest -q --require-cuda`; the CPU-only
command explicitly skips unavailable CUDA tests. Follow
`experiments/counterfactual/README.md` for timing reruns into a separate output
directory. Derived values do not establish cross-machine thresholds, industrial
prevalence, a new preconditioner or an online solver policy. The prior baseline and controlled extension are identified by
https://doi.org/10.5281/zenodo.22668106. The earlier baseline DOI
10.5281/zenodo.22303525 identifies the retained baseline measurements only.
