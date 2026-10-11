from __future__ import annotations

import csv
import math
from datetime import datetime, timezone
from collections import Counter, defaultdict
from pathlib import Path
from re import split, sub
import zipfile
from xml.sax.saxutils import escape

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "template" / "icemce2026" / "WordGuidelines" / "WordGuidelines" / "IOP-ConfSer-template.docx"
OUT = ROOT / "paper" / "icemce2026_iop_manuscript.docx"
FIG_DIR = ROOT / "paper" / "figures"
RAW_DIR = ROOT / "results" / "raw"
LINE_SPACING = 1.0
EQUATION_LINE_SPACING = 1.14
EQUATION_SPACE_BEFORE_PT = 3
EQUATION_SPACE_AFTER_PT = 3


REFERENCES = [
    'Virtanen P, Gommers R, Oliphant T E, Haberland M, Reddy T, Cournapeau D et al 2020 SciPy 1.0: fundamental algorithms for scientific computing in Python Nature Methods 17 261-272. doi:10.1038/s41592-019-0686-2',
    'Harris C R, Millman K J, van der Walt S J, Gommers R, Virtanen P, Cournapeau D et al 2020 Array programming with NumPy Nature 585 357-362. doi:10.1038/s41586-020-2649-2',
    'Lam S K, Pitrou A and Seibert S 2015 Numba: a LLVM-based Python JIT compiler Proc. Second Workshop on the LLVM Compiler Infrastructure in HPC 1-6. doi:10.1145/2833157.2833162',
    'Bell N, Olson L N, Schroder J and Southworth B 2023 PyAMG: algebraic multigrid solvers in Python Journal of Open Source Software 8 5495. doi:10.21105/joss.05495',
    'Strikwerda J C 2004 Finite Difference Schemes and Partial Differential Equations 2nd edn (Philadelphia: SIAM). doi:10.1137/1.9780898717938',
    'Hestenes M R and Stiefel E 1952 Methods of conjugate gradients for solving linear systems Journal of Research of the National Bureau of Standards 49 409-436. doi:10.6028/jres.049.044',
    'Saad Y 2003 Iterative Methods for Sparse Linear Systems 2nd edn (Philadelphia: SIAM). doi:10.1137/1.9780898718003',
    'Ruge J W and Stuben K 1987 Algebraic multigrid in McCormick S F (ed) Multigrid Methods (Philadelphia: SIAM) 73-130. doi:10.1137/1.9781611971057.ch4',
    "Bernaschi M, Celestini A, Richelli G and D'Ambra P 2026 On the energy efficiency of sparse matrix computations on multi-GPU clusters Future Generation Computer Systems 183 108519. doi:10.1016/j.future.2026.108519",
    'Welter A and Nguyen N C 2026 Preconditioning techniques for hybridizable discontinuous Galerkin discretizations on GPU architectures Computer Methods in Applied Mechanics and Engineering 456 118951. doi:10.1016/j.cma.2026.118951',
    'Yuan F, Yang X, Huang Y, Dong D, Xu C, Liu J et al 2025 CRAMG: a communication-reduced algebraic multigrid method Proc. 39th ACM International Conference on Supercomputing 397-411. doi:10.1145/3721145.3725764',
    'Green D, Hu X, Lore J, Mu L and Stowell M L 2022 An efficient high-order numerical solver for diffusion equations with strong anisotropy Computer Physics Communications 276 108333. doi:10.1016/j.cpc.2022.108333',
    "Koskela T, Christidi I, Giordano M, Dubrovska E, Quinn J, Maynard C et al 2023 Principles for automated and reproducible benchmarking Proc. SC '23 Workshops 609-618. doi:10.1145/3624062.3624133",
    'Standard Performance Evaluation Corporation 2021 734.hpgmgfv_m: SPEChpc 2021 Benchmark Description. https://www.spec.org/hpc2021/docs/benchmarks/734.hpgmgfv_m.html accessed 8 September 2026',
    'Lawrence Livermore National Laboratory n.d. AMG2023: ATS-6 Benchmarks documentation. https://software.llnl.gov/benchmarks/10_amg/amg.html accessed 8 September 2026',
    "D'Ambra P, Durastante F, Filippone S and Zikatanov L 2023 Automatic coarsening in algebraic multigrid utilizing quality measures for matching-based aggregations Computers & Mathematics with Applications 144 290-305. doi:10.1016/j.camwa.2023.06.026",
    'Anzt H, Cojean T, Flegar G, Göbel F, Grützmacher T, Nayak P et al 2022 Ginkgo: a modern linear operator algebra framework for high performance computing ACM Transactions on Mathematical Software 48 2:1-2:33. doi:10.1145/3480935',
    'Pekkila J, Lappi O, Robertsen F and Korpi-Lagg M J 2025 Stencil computations on AMD and Nvidia graphics processors: performance and tuning strategies Concurrency and Computation: Practice and Experience 37 e70129. doi:10.1002/cpe.70129',
    'Makhmut Y, Imankulov T, Gorlatch S and Matkerim B 2026 A CUDA performance study of global- and shared-memory kernels for the Buckley-Leverett polymer-flooding problem Applied Sciences 16 5449. doi:10.3390/app16115449',
    'Tsai Y-H M, Beams N and Anzt H 2023 Three-precision algebraic multigrid on GPUs Future Generation Computer Systems 149 280-293. doi:10.1016/j.future.2023.07.024',
    'Graillat S, Jézéquel F, Mary T and Molina R 2024 Adaptive precision sparse matrix-vector product and its application to Krylov solvers SIAM Journal on Scientific Computing 46 C30-C56. doi:10.1137/22M1522619',
    'Aksoylu B, Graham I G, Klie H and Scheichl R 2008 Towards a rigorously justified algebraic preconditioner for high-contrast diffusion problems Computing and Visualization in Science 11 319-331. doi:10.1007/s00791-008-0105-1',
    'Aksoylu B and Yeter Z 2010 Robust multigrid preconditioners for cell-centered finite volume discretization of the high-contrast diffusion equation Computing and Visualization in Science 13 229-245. doi:10.1007/s00791-010-0140-6',
    'Carson E, Liesen J and Strakos Z 2024 Towards understanding CG and GMRES through examples Linear Algebra and its Applications 692 241-291. doi:10.1016/j.laa.2024.04.003',
    'Firmbach M, Phillips M, Glusa C, Popp A, Siefert C M and Mayr M 2026 Smoothed aggregation algebraic multigrid for problems with heterogeneous and anisotropic materials arXiv:2602.05686 (preprint). doi:10.48550/arXiv.2602.05686',
    'Funk Y, Götz M and Anzt H 2022 Prediction of optimal solvers for sparse linear systems using deep learning Proc. 2022 SIAM Conference on Parallel Processing for Scientific Computing 14-24. doi:10.1137/1.9781611977141.2',
    'Sun H-B, Jing Y-F and Xu X-W 2025 A new matrix feature selection strategy in machine learning models for certain Krylov solver prediction Journal of Classification 42 72-89. doi:10.1007/s00357-024-09484-0',
    'Xiong H, Yang W, He W, Lin S, Li K and Li K 2025 MM-AutoSolver: a multimodal machine learning method for the auto-selection of iterative solvers and preconditioners Journal of Parallel and Distributed Computing 205 105144. doi:10.1016/j.jpdc.2025.105144',
    'Zabegaev Y, Keilegavlen E, Iversen E and Berre I 2024 Automated linear solver selection for simulation of multiphysics processes in porous media Computer Methods in Applied Mechanics and Engineering 426 117031. doi:10.1016/j.cma.2024.117031',
    'Patankar S V 1980 Numerical Heat Transfer and Fluid Flow 1st edn (New York: Hemisphere). ISBN:9780891165224',
    'Hoefler T and Belli R 2015 Scientific benchmarking of parallel computing systems: twelve ways to tell the masses when reporting performance results Proc. International Conference for High Performance Computing, Networking, Storage and Analysis (SC15) 73:1-73:12. doi:10.1145/2807591.2807644',
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def portfolio_table_rows() -> list[list[str]]:
    rows = read_csv_rows(ROOT / "results/analysis/counterfactual/portfolio_translation_floors.csv")
    methods = {"jacobi": "J", "amg0": "SA", "rs025": "RS"}
    return [[r["n"], {"two_by_eight": "2x8", "three_by_six": "3x6"}[r["motif"]],
             {"odd_x": "Odd-x", "random": "Random"}[r["rhs"]],
             methods[r["centered_winner"]], methods[r["shifted_winner"]],
             "Yes" if r["both_stable"] == "True" else "No",
             f"{100*float(r['empirical_minimum_mean_excess']):.2f}"] for r in rows]


def estimate_order(h_values: list[float], errors: list[float]) -> float:
    log_h = [math.log(value) for value in h_values]
    log_e = [math.log(value) for value in errors]
    mean_h = sum(log_h) / len(log_h)
    mean_e = sum(log_e) / len(log_e)
    numerator = sum((h - mean_h) * (e - mean_e) for h, e in zip(log_h, log_e))
    denominator = sum((h - mean_h) ** 2 for h in log_h)
    return numerator / denominator


def sci_plain(value: float, precision: int = 2) -> str:
    return f"{value:.{precision}e}".replace("e-0", "e-").replace("e+0", "e+")


def method_label(method: str, threads: str | None = None) -> str:
    labels = {
        "cg": "CG",
        "jacobi-pcg": "Jacobi-PCG",
        "amg-pcg": "AMG-PCG",
        "numpy-vectorized": "NumPy",
        "numba-serial": "Numba serial",
        "cuda-kernel": "CUDA kernel",
        "numba-parallel-cpu": "CPU Numba",
        "linear_cpu_vs_cuda": "Unvalidated fit intersection",
    }
    if method == "numba-parallel":
        return f"Numba parallel, {threads} threads"
    return labels.get(method, method)


def bool_value(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def convergence_table_rows() -> list[list[str]]:
    rows = read_csv_rows(RAW_DIR / "convergence.csv")
    by_case: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_case.setdefault(row["case_name"], []).append(row)
    output: list[list[str]] = []
    for case_name, label in [
        ("smooth_constant", "Constant coefficient"),
        ("smooth_variable", "Smooth variable coefficient"),
    ]:
        case_rows = sorted(by_case[case_name], key=lambda item: int(item["n"]))
        hs = [float(row["h"]) for row in case_rows]
        l2_errors = [float(row["l2_error"]) for row in case_rows]
        linf_errors = [float(row["linf_error"]) for row in case_rows]
        finest = case_rows[-1]
        output.append(
            [
                label,
                f"{estimate_order(hs, l2_errors):.2f}",
                f"{estimate_order(hs, linf_errors):.2f}",
                sci_plain(float(finest["l2_error"])),
                sci_plain(float(finest["residual_norm"])),
            ]
        )
    return output


def interface_verification_rows() -> list[list[str]]:
    rows = read_csv_rows(RAW_DIR / "interface_verification.csv")
    grouped = {
        (int(row["n"]), row["face_average"]): row
        for row in rows
    }
    output: list[list[str]] = []
    for n in sorted({key[0] for key in grouped}):
        arithmetic = grouped[(n, "arithmetic")]
        harmonic = grouped[(n, "harmonic")]
        output.append(
            [
                str(n),
                sci_plain(float(arithmetic["l2_error"])),
                sci_plain(float(harmonic["l2_error"])),
                sci_plain(float(arithmetic["flux_error_abs"])),
                sci_plain(float(harmonic["flux_error_abs"])),
            ]
        )
    return output


def solver_table_rows() -> list[list[str]]:
    rows = read_csv_rows(RAW_DIR / "solver_benchmark.csv")
    rows_256 = [row for row in rows if int(row["n"]) == 256]
    output: list[list[str]] = []
    for case_name, label in [
        ("smooth_variable_solver", "Smooth variable"),
        ("high_contrast_solver", "High contrast"),
    ]:
        for method in ["cg", "jacobi-pcg", "amg-pcg"]:
            row = next(
                item
                for item in rows_256
                if item["case"] == case_name and item["method"] == method
            )
            output.append(
                [
                    label,
                    method_label(method),
                    row["iterations"],
                    f"{float(row['total_seconds']):.3f}",
                    sci_plain(float(row["residual_norm"])),
                ]
            )
    return output


def performance_table_rows() -> list[list[str]]:
    cpu_rows = read_csv_rows(RAW_DIR / "cpu_scaling.csv")
    gpu_rows = read_csv_rows(RAW_DIR / "gpu_stencil.csv")
    cpu_by_key = {
        (row["method"], row["threads"]): row
        for row in cpu_rows
        if int(row["n"]) == 2048
    }
    output: list[list[str]] = []
    for method, threads in [
        ("numpy-vectorized", "1"),
        ("numba-serial", "1"),
        ("numba-parallel", "4"),
    ]:
        row = cpu_by_key[(method, threads)]
        output.append(
            [
                "CPU stencil",
                method_label(method, threads),
                row["n"],
                f"{float(row['seconds_per_apply']):.4g} s/apply",
                f"{float(row['estimated_gbytes_per_second']):.2f} GB/s",
            ]
        )
    for row in sorted(
        [
            item
            for item in gpu_rows
            if item["method"] == "cuda-kernel" and int(item["n"]) in {2048, 4096}
        ],
        key=lambda item: int(item["n"]),
    ):
        output.append(
            [
                "GPU crossover",
                method_label(row["method"]),
                row["n"],
                f"{sci_plain(float(row['seconds_per_step']))} s/step",
                f"{float(row['speedup_vs_cpu']):.2f}x vs CPU",
            ]
        )
    return output


def coefficient_difficulty_rows() -> list[list[str]]:
    decision_rows = read_csv_rows(RAW_DIR / "solver_decision_map.csv")
    conditioning_rows = read_csv_rows(RAW_DIR / "conditioning.csv")
    max_conditioning_n = max(int(row["n"]) for row in conditioning_rows)
    condition_by_case = {
        row["coefficient_case"]: row
        for row in conditioning_rows
        if int(row["n"]) == max_conditioning_n
    }
    metrics_by_case: dict[str, dict[str, str]] = {}
    for row in decision_rows:
        if int(row["n"]) == 64:
            metrics_by_case[row["coefficient_case"]] = row

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in metrics_by_case.values():
        grouped[row["family"]].append(row)

    rows: list[list[str]] = []
    for family in ["constant", "smooth", "inclusion", "layered", "checkerboard"]:
        candidates = grouped.get(family, [])
        if not candidates:
            continue
        row = max(candidates, key=lambda item: float(item["contrast_target"]))
        condition = condition_by_case.get(row["coefficient_case"])
        rows.append(
            [
                row["coefficient_case"],
                row["family"].title(),
                f"{float(row['contrast_observed']):.1f}",
                f"{float(row['grad_logk_inf']):.2f}",
                f"{float(row['total_variation_proxy']):.2f}",
                sci_plain(float(condition["condition_estimate"])) if condition is not None else "-",
            ]
        )
    return rows


def difficulty_relationship_rows() -> list[list[str]]:
    raw_rows = read_csv_rows(RAW_DIR / "difficulty_relationships.csv")
    pooled_rows = [row for row in raw_rows if row["n_group"] == "all"]
    by_key = {(row["descriptor"], row["response"]): row for row in pooled_rows}
    descriptors = [
        ("contrast_observed", "Cₖ contrast"),
        ("grad_logk_inf", "Gₖ(h) log-gradient"),
        ("total_variation_proxy", "Vₖ TV proxy"),
        ("condition_estimate", "κ(A) proxy"),
    ]

    def fixed_grid_text(descriptor: str, response: str) -> str:
        values = [
            float(row["spearman_rho"])
            for row in raw_rows
            if row["descriptor"] == descriptor
            and row["response"] == response
            and row["n_group"] != "all"
        ]
        if not values:
            return "-"
        values = sorted(values)
        midpoint = len(values) // 2
        if len(values) % 2 == 0:
            median_value = 0.5 * (values[midpoint - 1] + values[midpoint])
        else:
            median_value = values[midpoint]
        min_value = values[0]
        max_value = values[-1]
        if max_value - min_value < 0.005:
            return f"{median_value:.2f}"
        return f"{median_value:.2f} ({min_value:.2f}-{max_value:.2f})"

    descriptor_labels = {
        "contrast_observed": "Ck contrast",
        "grad_logk_inf": "Gk(h) log-gradient",
        "total_variation_proxy": "Vk TV proxy",
        "condition_estimate": "kappa(A) proxy",
    }
    rows: list[list[str]] = []
    for descriptor, label in descriptors:
        label = descriptor_labels.get(descriptor, label)
        cg = by_key.get((descriptor, "cg_iterations"))
        speedup = by_key.get((descriptor, "selected_speedup_vs_cg"))
        if cg is None and speedup is None:
            continue
        rows.append(
            [
                label,
                f"{float(cg['spearman_rho']):.2f}" if cg is not None else "-",
                fixed_grid_text(descriptor, "cg_iterations"),
                f"{float(speedup['spearman_rho']):.2f}" if speedup is not None else "-",
                fixed_grid_text(descriptor, "selected_speedup_vs_cg"),
            ]
        )
    return rows


def decision_summary_rows() -> list[list[str]]:
    rows = [row for row in read_csv_rows(RAW_DIR / "solver_decision_map.csv") if bool_value(row["is_best"])]
    grouped: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[int(row["n"])].append(row)

    output: list[list[str]] = []
    for n in sorted(grouped):
        group = grouped[n]
        counts = Counter(row["best_method"] for row in group)
        speedups = sorted(float(row["speedup_vs_cg"]) for row in group)
        median = speedups[len(speedups) // 2]
        if len(speedups) % 2 == 0:
            median = 0.5 * (speedups[len(speedups) // 2 - 1] + speedups[len(speedups) // 2])
        output.append(
            [
                str(n),
                str(len(group)),
                str(counts.get("cg", 0)),
                str(counts.get("jacobi-pcg", 0)),
                str(counts.get("amg-pcg", 0)),
                f"{median:.2f}",
                f"{max(speedups):.2f}",
            ]
        )
    return output


def averaging_sensitivity_rows() -> list[list[str]]:
    rows = read_csv_rows(RAW_DIR / "averaging_sensitivity.csv")
    by_key = {
        (row["coefficient_case"], int(row["n"]), row["face_average"], row["method"]): row
        for row in rows
    }

    def compact_method(method: str) -> str:
        return {
            "cg": "CG",
            "jacobi-pcg": "Jacobi",
            "amg-pcg": "AMG",
        }.get(method, method_label(method))

    output: list[list[str]] = []
    for case in ["inclusion_c100", "layered_c100", "checkerboard_c100"]:
        for n in [64, 128, 256]:
            cg_a = by_key[(case, n, "arithmetic", "cg")]
            cg_h = by_key[(case, n, "harmonic", "cg")]
            jac_a = by_key[(case, n, "arithmetic", "jacobi-pcg")]
            jac_h = by_key[(case, n, "harmonic", "jacobi-pcg")]
            amg_a = by_key[(case, n, "arithmetic", "amg-pcg")]
            amg_h = by_key[(case, n, "harmonic", "amg-pcg")]
            best_a = next(
                row
                for row in rows
                if row["coefficient_case"] == case
                and int(row["n"]) == n
                and row["face_average"] == "arithmetic"
                and bool_value(row["is_best"])
            )
            best_h = next(
                row
                for row in rows
                if row["coefficient_case"] == case
                and int(row["n"]) == n
                and row["face_average"] == "harmonic"
                and bool_value(row["is_best"])
            )
            output.append(
                    [
                        case,
                        str(n),
                        f"{float(cg_a['iterations']):.0f}/{float(cg_h['iterations']):.0f}",
                        f"{float(jac_a['iterations']):.0f}/{float(jac_h['iterations']):.0f}",
                        f"{float(amg_a['iterations']):.0f}/{float(amg_h['iterations']):.0f}",
                        f"{compact_method(best_a['method'])}/{compact_method(best_h['method'])}",
                        f"{float(best_a['speedup_vs_cg']):.2f}/{float(best_h['speedup_vs_cg']):.2f}",
                    ]
            )
    return output


def timing_stability_rows() -> list[list[str]]:
    rows = read_csv_rows(RAW_DIR / "timing_stability.csv")
    selected = sorted(rows, key=lambda item: (int(float(item["n"])), item["coefficient_case"]))

    output: list[list[str]] = []
    for row in selected:
        status = "stable" if bool_value(row["decision_stable"]) else "variable"
        output.append(
            [
                row["coefficient_case"],
                str(int(float(row["n"]))),
                method_label(row["best_method_by_median"]),
                method_label(row["best_method_vote"]),
                f"{float(row['vote_fraction']):.2f}",
                f"{float(row['median_speedup_vs_cg']):.2f}",
                f"{100.0 * float(row['selected_rel_iqr']):.1f}%",
                status,
            ]
        )
    return output


def hardware_model_rows() -> list[list[str]]:
    rows = read_csv_rows(RAW_DIR / "hardware_crossover_model.csv")
    by_component = {row["model_component"]: row for row in rows}
    cpu = by_component["cpu"]
    cuda = by_component["cuda"]
    crossover = by_component["crossover"]
    return [
        [
            "CPU Numba",
            str(int(float(cpu["observations"]))),
            sci_plain(float(cpu["beta_seconds_per_unknown"]), precision=3),
            f"{float(cpu['r2']):.3f}",
            "-",
        ],
        [
            "CUDA kernel",
            str(int(float(cuda["observations"]))),
            sci_plain(float(cuda["beta_seconds_per_unknown"]), precision=3),
            f"{float(cuda['r2']):.3f}",
            "-",
        ],
        [
            "Unvalidated fit intersection",
            "-",
            "-",
            f"{float(crossover['r2']):.3f}",
            f"{float(crossover['crossover_grid_n']):.0f}",
        ],
    ]


def normalize_docx_revision(path: Path) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with zipfile.ZipFile(path, "r") as zin, zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "docProps/core.xml":
                text = data.decode("utf-8")
                text = sub(r"<cp:revision>.*?</cp:revision>", "<cp:revision>1</cp:revision>", text)
                data = text.encode("utf-8")
            zout.writestr(item, data)
    tmp_path.replace(path)


def clear_body(doc: Document) -> None:
    body = doc._element.body
    for child in list(body):
        if child.tag == qn("w:sectPr"):
            continue
        body.remove(child)


def style_name(doc: Document, preferred: str, fallback: str = "Normal") -> str:
    names = {style.name for style in doc.styles}
    return preferred if preferred in names else fallback


def set_document_defaults(doc: Document) -> None:
    section = doc.sections[0]
    section.orientation = WD_ORIENT.PORTRAIT
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(4.0)
    section.bottom_margin = Cm(2.7)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)
    section.header_distance = Cm(0)
    section.footer_distance = Cm(0)

    for style in doc.styles:
        if hasattr(style, "font"):
            style.font.name = "Times New Roman"
            style.font.size = style.font.size or Pt(10)
            if style._element.rPr is not None:
                style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        if hasattr(style, "paragraph_format"):
            fmt = style.paragraph_format
            fmt.line_spacing = LINE_SPACING
            if fmt.space_after is None:
                fmt.space_after = Pt(0)


def normalize_runs(paragraph) -> None:
    for run in paragraph.runs:
        run.font.name = "Times New Roman"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")


def add_runs_with_citations(paragraph, text: str) -> None:
    parts = split(r"(\[\[[^\]]+\]\])", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("[[") and part.endswith("]]"):
            citation = part[2:-2]
            run = paragraph.add_run(f"[{citation}]")
            run.font.superscript = True
            run.font.name = "Times New Roman"
        else:
            run = paragraph.add_run(part)
            run.font.name = "Times New Roman"
            run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")


def add_paragraph(doc: Document, text: str, style: str, align=None):
    p = doc.add_paragraph(style=style)
    if align is not None:
        p.alignment = align
    add_runs_with_citations(p, text)
    normalize_runs(p)
    return p


def add_section(doc: Document, number: int, title: str) -> None:
    p = doc.add_paragraph(style=style_name(doc, "IOP-CS-SectionHead"))
    p.add_run(f"{number}. {title}")
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.keep_together = True
    normalize_runs(p)


def add_subsection(doc: Document, number: str, title: str) -> None:
    p = doc.add_paragraph(style=style_name(doc, "IOP-CS-SubsectionHeading"))
    p.add_run(f"{number}. {title}")
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.keep_together = True
    normalize_runs(p)


def no_borders(table) -> None:
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = OxmlElement(f"w:{edge}")
        tag.set(qn("w:val"), "nil")
        borders.append(tag)
    tbl_pr.append(borders)


def math_text(text: str) -> str:
    return f'<m:r><m:t xml:space="preserve">{escape(text)}</m:t></m:r>'


def math_expr(value: str) -> str:
    return value if value.startswith("<m:") else math_text(value)


def math_seq(*parts: str) -> str:
    return "".join(math_expr(part) for part in parts)


def math_sub(base: str, subscript: str) -> str:
    return (
        "<m:sSub><m:e>"
        f"{math_expr(base)}"
        "</m:e><m:sub>"
        f"{math_expr(subscript)}"
        "</m:sub></m:sSub>"
    )


def math_sup(base: str, superscript: str) -> str:
    return (
        "<m:sSup><m:e>"
        f"{math_expr(base)}"
        "</m:e><m:sup>"
        f"{math_expr(superscript)}"
        "</m:sup></m:sSup>"
    )


def math_frac(numerator: str, denominator: str) -> str:
    return (
        '<m:f><m:fPr><m:type m:val="bar"/></m:fPr><m:num>'
        f"{math_expr(numerator)}"
        "</m:num><m:den>"
        f"{math_expr(denominator)}"
        "</m:den></m:f>"
    )


def equation_omml_lines(text: str, number: int) -> list[str]:
    if number == 1:
        return [
            math_seq(
                "−∇·(k(x,y)∇u(x,y)) = f(x,y),  (x,y) ∈ ",
                math_sup("(0,1)", "2"),
            )
        ]
    if number == 2:
        return [math_seq("k(x,y) = 1 + 0.5 sin(2πx) sin(2πy)")]
    if number == 3:
        return [
            math_seq("k(x,y) = 1 + 99 ", math_sub("χ", "D"), "(x,y)"),
            math_seq(
                "D = { (x,y) : ",
                math_sup("(x-0.5)", "2"),
                " + ",
                math_sup("(y-0.5)", "2"),
                " < ",
                math_sup("0.15", "2"),
                " }",
            ),
        ]
    if number == 4:
        return [
            math_seq(
                math_sub("C", "k"),
                " = ",
                math_frac("max(k)", "min(k)"),
                ",   ",
                math_sup(math_sub("G", "k"), "(h)"),
                " = ",
                math_sub(math_seq("||", math_sub("∇", "h"), " log(k)||"), "∞"),
            ),
            math_seq(
                math_sub("V", "k"),
                " = ",
                math_frac(math_seq("Σ|", math_sub("Δ", "x"), "k| + Σ|", math_sub("Δ", "y"), "k|"), "N−1"),
            ),
        ]
    if number == 5:
        return [
            math_seq(math_sub("(Au)", "ij"), " = "),
            math_seq(
                math_sub("k", "i+1/2,j"),
                math_frac(math_seq(math_sub("u", "ij"), " - ", math_sub("u", "i+1,j")), math_sup("h", "2")),
                " + ",
                math_sub("k", "i-1/2,j"),
                math_frac(math_seq(math_sub("u", "ij"), " - ", math_sub("u", "i-1,j")), math_sup("h", "2")),
            ),
            math_seq(
                "+ ",
                math_sub("k", "i,j+1/2"),
                math_frac(math_seq(math_sub("u", "ij"), " - ", math_sub("u", "i,j+1")), math_sup("h", "2")),
                " + ",
                math_sub("k", "i,j-1/2"),
                math_frac(math_seq(math_sub("u", "ij"), " - ", math_sub("u", "i,j-1")), math_sup("h", "2")),
            ),
        ]
    if number == 6:
        return [math_seq(math_sub("u", "exact"), "(x,y) = sin(πx) sin(πy)")]
    if number == 7:
        return [
            math_seq(
                math_sup("s", "*"),
                "(c,N) = ",
                math_sub("arg min", "s ∈ S"),
                " [",
                math_sub("T", "setup"),
                "(s,c,N) + ",
                math_sub("T", "solve"),
                "(s,c,N)]",
            )
        ]
    if number == 8:
        return [math_seq("S = ", math_sup("D", "−1/2"), " A ", math_sup("D", "−1/2"),
                         ",   g = ", math_sup("D", "−1/2"), " b,   Rb = −b")]
    if number == 9:
        return [math_seq("E(P) = ", math_sub("min", "s ∈ P"), " [",
                         math_frac("1", "2"), " ", math_sub("Σ", "j=0,1"), " ",
                         math_frac("T(j,s)", math_seq(math_sub("min", "t ∈ P"), " T(j,t)")),
                         "] − 1")]
    return [math_text(text)]


def add_math_to_paragraph(paragraph, text: str, number: int) -> None:
    xml = f'<m:oMath {nsdecls("m")}>{equation_omml_lines(text, number)[0]}</m:oMath>'
    paragraph._p.append(parse_xml(xml))


def add_equation(doc: Document, text: str, number: int) -> None:
    table = doc.add_table(rows=1, cols=3)
    table.allow_autofit = False
    no_borders(table)
    tr_pr = table.rows[0]._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement("w:cantSplit"))
    table.columns[0].width = Inches(0.55)
    table.columns[1].width = Inches(5.20)
    table.columns[2].width = Inches(0.55)
    spacer_cell = table.cell(0, 0)
    eq_cell = table.cell(0, 1)
    num_cell = table.cell(0, 2)
    spacer_cell.width = Inches(0.55)
    eq_cell.width = Inches(5.20)
    num_cell.width = Inches(0.55)
    lines = equation_omml_lines(text, number)
    for idx, line in enumerate(lines):
        eq_p = eq_cell.paragraphs[0] if idx == 0 else eq_cell.add_paragraph()
        eq_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        eq_p.paragraph_format.line_spacing = EQUATION_LINE_SPACING
        eq_p.paragraph_format.space_before = Pt(EQUATION_SPACE_BEFORE_PT if idx == 0 else 0)
        eq_p.paragraph_format.space_after = Pt(EQUATION_SPACE_AFTER_PT if idx == len(lines) - 1 else 0)
        eq_p.paragraph_format.keep_together = True
        eq_p.paragraph_format.keep_with_next = idx < len(lines) - 1
        xml = f'<m:oMath {nsdecls("m")}>{line}</m:oMath>'
        eq_p._p.append(parse_xml(xml))
    num_p = num_cell.paragraphs[0]
    num_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    num_p.paragraph_format.line_spacing = EQUATION_LINE_SPACING
    num_p.paragraph_format.keep_together = True
    num_p.add_run(f"({number})")
    normalize_runs(num_p)


def add_caption(doc: Document, text: str):
    p = doc.add_paragraph(style=style_name(doc, "IOP-CS-CaptionText"))
    p.add_run(text)
    normalize_runs(p)
    return p


def add_data_table(doc: Document, caption: str, headers: list[str], rows: list[list[str]]) -> None:
    caption_paragraph = add_caption(doc, caption)
    caption_paragraph.paragraph_format.keep_with_next = True
    caption_paragraph.paragraph_format.keep_together = True
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    header_cells = table.rows[0].cells
    for cell, header in zip(header_cells, headers):
        cell.text = header
        for paragraph in cell.paragraphs:
            paragraph.paragraph_format.keep_together = True
            paragraph.paragraph_format.keep_with_next = True
            normalize_runs(paragraph)
            for run in paragraph.runs:
                run.bold = True
                run.font.size = Pt(9)
    for row_index, row in enumerate(rows):
        table_row = table.add_row()
        tr_pr = table_row._tr.get_or_add_trPr()
        tr_pr.append(OxmlElement("w:cantSplit"))
        cells = table_row.cells
        for cell, value in zip(cells, row):
            cell.text = value
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.keep_together = True
                paragraph.paragraph_format.keep_with_next = row_index < len(rows) - 1
                normalize_runs(paragraph)
                for run in paragraph.runs:
                    run.font.size = Pt(9)
    if headers == ['Case', 'N', 'Monitored', 'Count-only', 'CG', 'J', 'SA']:
        table.autofit = False
        widths = [1.03, 0.42, 1.47, 1.47, 0.62, 0.62, 0.62]
        for col, width in zip(table.columns, widths):
            col.width = Inches(width)
        for row in table.rows:
            for cell, width in zip(row.cells, widths):
                cell.width = Inches(width)
    spacer = doc.add_paragraph()
    spacer.paragraph_format.line_spacing = 1.0
    spacer.paragraph_format.space_before = Pt(0)
    spacer.paragraph_format.space_after = Pt(2)
    spacer.add_run(" ").font.size = Pt(2)


def add_figure(doc: Document, filename: str, caption: str, width_inches: float = 4.85) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_together = True
    p.paragraph_format.keep_with_next = True
    run = p.add_run()
    run.add_picture(str(FIG_DIR / filename), width=Inches(width_inches))
    caption_paragraph = add_caption(doc, caption)
    caption_paragraph.paragraph_format.keep_together = True


def build() -> None:
    from build_compact_manuscript import build_compact
    build_compact()


if __name__ == "__main__":
    build()
