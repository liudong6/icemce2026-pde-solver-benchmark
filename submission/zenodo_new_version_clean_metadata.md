# Zenodo Clean Version Metadata

## Purpose

This release is Zenodo version v4 in the `10.5281/zenodo.22290959` version chain, with reserved DOI `10.5281/zenodo.22668106` and corresponding GitHub release `v1.1-icemce2026-submission`. The complete archive includes the revised manuscript and controlled extension. The earlier DOI `10.5281/zenodo.22303525` identifies the retained baseline measurements. `MANIFEST.sha256` identifies the exact upload files. Publication is verified separately against the public record and GitHub release.

## Title

A Coefficient-Aware Finite-Difference Benchmark for Solver Selection and CPU/GPU Stencil Scaling in Heat-Conduction Simulation

## Creators

Dong Liu; University of Nottingham Ningbo China

## Description

This archive contains the manuscript, source code, raw CSV evidence, generated figures and tables, environment requirements, and cold-start smoke-test log for a reproducible finite-difference benchmark of solver selection and CPU/GPU stencil scaling in heat-conduction simulation. The study verifies a conservative finite-difference operator, evaluates coefficient-aware solver decisions for CG, Jacobi-PCG, and AMG-PCG, and reports bounded CPU/Numba/CUDA stencil measurements on one workstation.

This revision specifies the residual-monitoring and first-use overhead included in solver timings, corrects the displayed total-variation descriptor normalisation to match the implementation, identifies the four-point hardware fit as exploratory rather than a validated crossover threshold, completes reference article-number information, and updates the AI-assistance disclosure and document layout. The 13 baseline raw files remain unchanged. New code and data add exact matched motifs, translation and source controls, fresh-setup timings, an independent motif family, perturbation tests, and preconditioned spectral diagnostics. There are 576 pilot and 2212 geometry/forcing follow-up solves, with pilot failures retained, plus 744 accepted portfolio-audit solves. The latter include a 504-solve confirmation interleaving field positions and candidate solvers; classical AMG changes the decision boundary while leaving three of twelve translated pairs with stable winner reversals. The new figure and complete summary tables are reproducible from the accompanying CSV files. The main text includes all 12 interleaved translated pairs, with an explicit empirical cost-floor definition; two routine sensitivity/timing tables remain in the supplementary artefact. An evidence map links numerical claims to their inputs and commands. The disclosure identifies AI assistance with experimental design, code implementation, numerical analysis and manuscript preparation, and records the author's independent review of the controlled experiments. A fresh CPU environment passes 91 tests with five explicit optional CUDA skips and reproduces 76 outputs byte-for-byte; a required-CUDA mode verifies all 96 tests in the existing CUDA environment. The resolved CPU dependency set and environment record accompany the artefact.

The manuscript also adds direct context from HPGMG-FV and AMG2023, removes five peripheral application references, distinguishes retrospective comparison from predictive solver selection, and presents all 15 existing repeated-timing case-size cells. The exploratory hardware-fit table is retained in the supplementary files rather than the main paper. The methods specify the AMG defaults and the historical reproducibility limits of random initialisation and unrecorded runtime settings.

## Keywords

- heat conduction
- finite difference method
- partial differential equations
- sparse linear solvers
- conjugate gradient
- algebraic multigrid
- performance scaling
- reproducible benchmark
- CPU/GPU stencil
- Numba CUDA

## Files

- `icemce2026_iop_manuscript.docx`
- `icemce2026_iop_manuscript.pdf`
- `supplementary_artefact.zip`
- `icemce2026_pde_solver_benchmark_v1.0_repository.zip`
