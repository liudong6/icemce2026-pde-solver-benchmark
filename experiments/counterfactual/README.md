# Matched-field and forcing audit

The controlled extension tests the sufficiency of coefficient descriptors by holding them exactly fixed while changing geometry, source symmetry or placement. It does not implement an automatic solver selector. Source/RHS dependence and Krylov invariant-subspace theory are established numerical-analysis facts.

Recorded measurements are in `results/raw/counterfactual`. Each run refuses to overwrite its existing output CSV. Numerical functions in these portable scripts are unchanged from the executed scripts; `source_provenance.json` records original and distributed hashes and the output-routing change.

From the repository root, with the pinned requirements installed:

```powershell
python experiments/analyze_counterfactual.py
python -m pytest
```

The first command regenerates all controlled summaries in `results/analysis/counterfactual` and the manuscript figure. Full timings are optional, slower, and hardware-dependent. Run the following sequentially; by default they create `results/raw/counterfactual_rerun`, preserving recorded evidence:

```powershell
python experiments/counterfactual/pilot.py
python experiments/counterfactual/confirmation.py
python experiments/counterfactual/heldout.py
python experiments/counterfactual/perturbation.py
python experiments/counterfactual/mechanism.py
python experiments/counterfactual/validate_spectrum.py
python experiments/counterfactual/analyze_pilot.py
python experiments/counterfactual/analyze_confirmation.py
```

Set `PDESCALE_COUNTERFACTUAL_OUTPUT` to a different empty directory for another rerun. The generic manuscript summary command intentionally reads the recorded data; inspect rerun CSVs separately before replacing any archived evidence.

The pilot is exploratory: 576 solves, including retained failed acceptance checks at extreme contrast and CG iteration limits. It uses rtol=1e-8 and an independent residual threshold of 1e-7. Follow-up data comprise 1440 confirmation, 640 independent-family, and 132 perturbation solves. These use rtol=1e-9 and an independent true residual threshold of 1e-8. Do not pool pilot and follow-up timing protocols.

Follow-ups warm imports and small solves, limit BLAS to one thread, shuffle method/source order, use zero initial guesses, record setup seeds and count iterations without a residual recomputation inside each callback. Each timed case constructs its preconditioner anew. SA uses symmetric strength with theta=0 and keep=True to retain hierarchy diagnostics; these are timings of that recorded configuration. Matrix assembly, source construction and final residual verification are outside the setup-plus-solve timer. No other numerical timing job for this project was run concurrently. Operating-system activity, clock frequencies and thermal state were not controlled or monitored; no cross-hardware claim is made.

Motifs are unit-grid binary arrays dilated into nodal coefficient fields. In both tested families their 12 occupied cells and 20 interface edges give exact histogram, contrast, total-variation and maximum-gradient matches. A transpose control transforms both geometry and source. Translation changes their relative placement; it does not change shape or component count. A symmetric source is a valid workload, but its runtime need not represent other sources.

All CSV rows, including unstable winners and failures, are retained. Summary bars use medians and full five-run ranges, not confidence intervals. The empirical invariant-only cost floor is the smaller of the two methods' mean normalised costs across an equally weighted centered/translated pair. It is a finite-sample descriptive quantity and is not a guaranteed population loss or a deployed selection rule. An equal-feature argument applies only to rules restricted to those features.

`mechanism.csv` contains offline spectral estimates, source overlaps and exploratory coarse-energy diagnostics. Jacobi scaling is symmetric; AMG BA is evaluated with a nonsymmetric eigensolver. Dense SPD-similar matrices on N=32 provide an independent numerical check. Spectral estimates are not rigorous enclosures, and the archive records the failed initial over-tight ARPACK validation attempt and its resolution. Source overlap below roundoff is reported only as near numerical zero. Reflection does not account for every other symmetry sector or spectrum change.

The older Zenodo DOI identifies baseline measurements. These new data require a new archive version before any claim that the complete extension is publicly archived under a version DOI.


## Candidate-solver sensitivity extension

The additional `portfolio.csv` contains 240 fresh-setup solves comparing Jacobi,
SA symmetric strength theta=0, SA theta=0.25, and classical Ruge-Stueben AMG.
`portfolio_confirmation.csv` contains 504 solves at N=128,160,192: seven repeats
interleave field positions, motifs, sources and methods within each N block.
The three-method confirmation retains 17/24 stable cells and 3/12 stable
translation reversals. The original N128 motif gives an 11.91% finite empirical
fixed-choice excess-cost floor; at N192 the median-based floor vanishes after
classical AMG is included. These are measured portfolio-conditional quantities,
not confidence bounds or population frequencies. The 3x6 anchor was used in
earlier experiments and is not described as an unseen geometry.

Both AMG families use V cycles, max_levels=10, max_coarse=10, retained hierarchy
diagnostics (keep=True), and the pseudoinverse coarse solver. SA retains the
recorded symmetric block Gauss-Seidel smoothers; classical AMG uses symmetric
Gauss-Seidel before and after coarse correction, RS splitting without a second
pass, classical interpolation and classical strength theta=0.25. Eight N32
dense checks verify numerical symmetry and positive definiteness of the inverse
preconditioners; they are not a general proof or a performance measurement.
All 744 new solves pass independent residual<=1e-8. Full settings, source hashes,
acceptance flags and summaries are retained. Assembly and final residual checks
remain outside timing. Screening and interleaved times must not be pooled.

```powershell
python experiments/counterfactual/portfolio.py
python experiments/counterfactual/portfolio_confirmation.py
python experiments/analyze_portfolio.py
```

The first two commands create separate rerun outputs, respecting
`PDESCALE_COUNTERFACTUAL_OUTPUT` and refusing existing destination CSV files.
The analysis command regenerates the recorded summaries from the archived CSVs.
The original DOI identifies baseline data only; these additions require the
complete revised archive's new version DOI before public submission.
