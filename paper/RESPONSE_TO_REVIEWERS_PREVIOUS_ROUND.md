Response to the reviewer

Manuscript: A Coefficient-Aware Finite-Difference Benchmark for Solver Selection and CPU/GPU Stencil Scaling in Heat-Conduction Simulation

Dear Editor and Reviewer,

Thank you for your comments. We have clarified why arithmetic averaging is retained in the main benchmark and how the different timing protocols limit the interpretation of solver choices. We have also added a paired experiment to measure the effect of residual monitoring. Below, we respond to the two points in your comment separately. Changes in the revised manuscript are highlighted in yellow.

1 Face averaging and physical interpretation

Reviewer comment

The primary two-dimensional benchmark uses arithmetic averaging of conductivity at cell faces, while the one-dimensional discontinuous-interface verification shows that harmonic averaging reproduces the analytical interface flux to roundoff and arithmetic averaging retains a grid-dependent interface error. Although a sensitivity analysis is provided for several discontinuous cases, the authors should more clearly justify why arithmetic averaging remains the primary operator for the main heat-conduction decision map and discuss how this choice affects the physical interpretation of discontinuous high-contrast material cases.

Response

We agree that the original presentation did not clearly separate the choice of a benchmark operator from the physical treatment of a material interface. We have revised Section 3 to make this distinction explicit. We retain arithmetic averaging to keep the main decision map consistent with the specified discrete benchmark and the historical comparisons. This is a reason for retaining the benchmark, not a claim that arithmetic averaging is the preferred interface law for composite heat conduction.

For an interface between two equal half-links, continuity of heat flux gives the harmonic coefficient 2ab/(a + b). We now explain this series-resistance argument and show why the two averages can differ substantially at a discontinuity. At a conductivity contrast of 100, the arithmetic-to-harmonic conductance ratio is 25.5025 on a mixed link. This ratio applies to the stated local interface model; it is not an estimate of the error in the temperature field.

We have also brought all nine arithmetic/harmonic comparisons into Table 6. The measured solver winner is unchanged in these single-pass comparisons, but the iteration counts are not: for example, AMG takes 13 and 28 iterations for the two averages in the checkerboard case at N = 64. We therefore explicitly state that agreement in the winner does not establish equivalent operators or equal physical accuracy.

The revised discussion limits the high-contrast arithmetic results to solver performance for that discrete operator. The one-dimensional test verifies aligned interface flux, whereas the two-dimensional comparison tests sensitivity of solver cost. We have not established accuracy at curved interfaces. Section 6 now advises choosing the face law from the interface geometry and resistance model before interpreting solver costs. The controlled matched-field study includes both averages. We have added Patankar’s Numerical Heat Transfer and Fluid Flow as reference [26] for the interface-conductivity context.

Revised locations: Section 3; Section 5.2 and Table 6; Section 6.

2 Timing protocols and solver boundaries

Reviewer comment

The manuscript employs different timing protocols for the baseline decision map and the controlled matched-field extension. In the baseline runs, residual-monitoring callbacks add an extra sparse matrix-vector product at every iteration and the first AMG setup may include import overhead, whereas the controlled extension uses count-only callbacks, warm imports, shuffled execution order, and controlled BLAS threading. Although the manuscript states that these results are not pooled, the distinction should be made more explicit when drawing conclusions across the two experimental sections, since the measured setup-inclusive solver boundaries may depend on these timing conditions.

Response

We agree that stating that the timings were not pooled was insufficient. We have revised Section 4 and the discussion and conclusions to specify which results belong to each protocol. The historical decision map describes the monitored implementation, including its setup and first-use costs. The translation reversals and empirical excess-cost floors are comparisons within the controlled extension. We do not transfer time ratios or solver boundaries between these experiments.

To test the effect of the callback directly, we added a paired calibration in Section 5.3 and Table 7. It covers three coefficient cases, three grid sizes, three solvers, two callback modes and seven repeats, giving 378 solves. Within each pair, we keep the operator, source, stopping tolerance and setup seed fixed. Imports are warmed, BLAS is limited to one thread, execution order is shuffled, and each solve uses a fresh preconditioner. All solves satisfy an independently checked relative residual of at most 1e−8; all 189 pairs have identical solution hashes and iteration counts.

The median paired monitored/count-only solve-time ratios range from 1.54 to 1.84 for CG, 1.58 to 1.77 for Jacobi-PCG, and 1.03 to 1.06 for AMG-PCG. Thus, monitoring affects the reported speedups differently across methods. It does not change the median winner in the nine calibration cells. We also report the variability: for constant conductivity at N = 256, count-only AMG has the lowest method median but wins only three of seven repeats. The supplementary summaries retain the timings and quartiles for every candidate.

Some N = 128 winners differ from the historical map under both callback modes. We cannot attribute these differences to callback removal alone. The new calibration does not reconstruct the historical cold-import, execution-order, threading or machine-state effects, and we have stated this limitation explicitly. We therefore do not claim a universal N = 128 crossover to AMG. Reference [27], by Hoefler and Belli, supports the discussion of performance-measurement practice.

Revised locations: Section 4; Section 5.3 and Table 7; Sections 6 and 7.

The new calibration data, analysis scripts and complete summaries are included in the revised supplementary material, archived at https://doi.org/10.5281/zenodo.22874266. The historical raw measurements have been retained unchanged.

Thank you for helping us make the scope and interpretation of the results clearer.

Sincerely,
The authors
