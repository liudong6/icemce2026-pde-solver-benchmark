# Response to the second-round review

Manuscript: *A Coefficient-Aware Finite-Difference Benchmark for Solver Selection and CPU/GPU Stencil Scaling in Heat-Conduction Simulation*

Revision: 20 September 2026. Section and table numbers refer to the revised manuscript. This draft has not been submitted.

Thank you for identifying the need to clarify the interface discretisation and the interpretation of measurements collected under different timing protocols. The revision addresses both concerns and adds a dedicated paired callback calibration. The historical raw measurements remain unchanged. Additions and replacements relative to the previous reviewed manuscript are highlighted in yellow in the revised Word document and its PDF export.

## 1. Primary face averaging and physical interpretation

**Comment, summarised:** Justify retaining arithmetic averaging in the two-dimensional decision map despite the aligned one-dimensional verification favouring harmonic averaging, and clarify the physical meaning of high-contrast material cases.

**Response:** Section 3 now explains that arithmetic averaging is retained to preserve the specified discrete benchmark and its historical comparisons. This choice is not presented as the preferred interface law for composite heat conduction. For two equal half-links, continuity of flux gives a resistance of h/(2a) + h/(2b), yielding the harmonic coefficient 2ab/(a+b). Its difference from the arithmetic coefficient is (a−b)²/[2(a+b)]: this is O(h²) for smooth positive conductivity but need not be small at a discontinuity. At contrast 100, the arithmetic-to-harmonic conductance ratio on a mixed link is 25.5025. The manuscript explicitly restricts this statement to the half-link interface assumption; it is not a global temperature-error estimate.

Table 6 now presents all nine existing contrast-100 case-size comparisons, including the iteration counts of all three solvers under both averages. Although the measured winner is unchanged in these single-pass comparisons, some iteration counts differ substantially—for example, checkerboard AMG at N = 64 requires 13 versus 28 iterations. The text therefore separates solver-cost sensitivity from physical solution accuracy. It also distinguishes the aligned one-dimensional flux verification from the two-dimensional operator comparison. The controlled matched-field extension includes both face averages.

Section 6 states the practical implication: the face law should be chosen from the material-interface geometry and resistance model before interpreting solver costs. Curved-interface accuracy has not been established by these experiments; neither averaging rule is claimed to resolve that issue automatically. Reference [26] supplies directly relevant numerical heat-transfer context.

**Locations:** Section 3; Section 5.2 and Table 6; Section 6.

## 2. Different timing protocols and conditional solver boundaries

**Comment, summarised:** Make the distinction between the historical monitored decision map and the controlled count-only extension more explicit when drawing conclusions, because setup-inclusive solver boundaries may depend on timing conditions.

**Response:** Section 4 now distinguishes three evidence groups: the historical monitored runs, the controlled matched-field extension, and a new paired callback calibration. It specifies callback behaviour, import treatment, execution order, threading, setup seeds, stopping tolerance and timing boundaries. Historical speedups describe the monitored implementation; translation reversals and empirical excess-cost floors are comparisons within their respective controlled experiments. No time ratios or winner boundaries are pooled across these groups.

The new Section 5.3 and Table 7 report a prospectively specified calibration: three coefficient cases, three grid sizes, three methods, two callback modes and seven repeats, totalling 378 solves. Within the calibration, the operator, source, tolerance, warm imports, single BLAS thread and paired setup seeds are fixed; the jobs are shuffled within each repeat. Each solve uses a fresh preconditioner. All 378 solves pass an independent true-residual threshold of 1e−8. All 189 callback-mode pairs have identical solution hashes and iteration counts.

Across the nine case-size cells, median paired monitored/count-only solve-time ratios range from 1.54 to 1.84 for CG, 1.58 to 1.77 for Jacobi-PCG, and 1.03 to 1.06 for AMG-PCG. The median winner does not change between callbacks in this calibration. We report this negative result together with unstable repeat-level choices: for constant conductivity at N = 256, count-only AMG has the lowest method median but wins only three of seven repeats. Complete candidate timings, quartiles and paired ratios accompany the manuscript.

Several N = 128 winners differ from the historical map under both callback modes. The revision explicitly states that removing the callback alone cannot explain that historical-to-calibration difference. Cold-import overhead and the historical effects of ordering, unrecorded threading and machine state cannot be separated retrospectively from the available measurements. We retain this limitation rather than subtracting estimated overhead from historical timings. No universal N = 128 AMG crossover is claimed. Reference [27] provides directly relevant performance-benchmarking context.

**Locations:** Section 4; Section 5.3 and Table 7; Sections 6–7. Reproduction inputs and commands: `experiments/protocol_sensitivity.md`, `results/raw/protocol_sensitivity`, and `experiments/analyze_protocol_sensitivity.py`.

## Availability of revision evidence

The accompanying supplementary package includes the new calibration, complete generated summaries and reproduction instructions. The prior published v4 DOI identifies the earlier baseline and controlled extension; it does not yet identify these additional calibration files. The complete revised artefact, including the new calibration, is identified by Zenodo v5 (https://doi.org/10.5281/zenodo.22874266) and GitHub release v1.2-icemce2026-review-revision. The recorded AI-assistance disclosure remains in the manuscript.
