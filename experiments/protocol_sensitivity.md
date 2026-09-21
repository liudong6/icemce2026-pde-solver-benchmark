# Residual-monitoring sensitivity calibration

This prospective protocol isolates one timing choice: a true-residual callback
versus a count-only callback. It does not recreate the historical import, BLAS,
power-state or fixed-order conditions and does not replace archived timings.

Fixed design: constant, inclusion_c100 and checkerboard_c100 at N=64,128,256;
arithmetic faces; unit right-hand side; homogeneous Dirichlet boundaries;
CG, Jacobi-PCG and the baseline default PyAMG SA-PCG configuration. Seven
repeats run both callback modes, with a fresh setup for every solve: 378 solves.
Each repeat shuffles all 54 case/grid/method/mode jobs with order seed 20092026.
Setup seed is 200920+repeat and is reset before every setup so each callback
pair uses the same seeded preconditioner construction. PyAMG is imported before
any recorded timer; all methods and modes receive a small-grid warm-up. BLAS
thread pools are limited to one during warm-up and measurements.

Use the original preconditioner helpers, zero-start SciPy CG, rtol=1e-8,
atol=0 and maxiter=12000. Both modes count iterations. The monitored mode uses
the original residual helper, including its RHS-norm computation and history
append on every iteration. The count-only mode only increments a counter.
Assembly, RHS construction, the final independent residual calculation and
solution hashing are outside setup-plus-solve timing. Accept a solve only when
SciPy reports success and its independently checked relative residual is at
most 1e-8. Retain all failures and do not select a winner for an incomplete or
failed case/mode cell. Do not retune tolerance or choose a favorable subset
after observing results.

Report every one of the 18 case/mode cells and nine paired case comparisons.
For each candidate, give median setup, solve and total times, full repeat
ranges, and paired monitored/count-only total-time ratios. Report per-repeat
winner consistency and whether the two median winners differ; a changed label
is not a statistically established reversal. Compare iteration counts and
solution hashes within each matched pair. No winner count or speedup threshold
is a required outcome. Do not pool these measurements with earlier protocols,
subtract the measured overhead from old CSV values, or treat the check as an
isolation of all historical timing confounders.

Run `python experiments/run_protocol_sensitivity.py` to a new rerun directory;
it refuses existing output. The recorded calibration and environment are in
`results/raw/protocol_sensitivity`. Regenerate summaries without rerunning
timings using `python experiments/analyze_protocol_sensitivity.py`.
