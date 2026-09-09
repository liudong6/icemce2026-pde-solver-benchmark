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
    'Briggs W L, Henson V E and McCormick S F 2000 A Multigrid Tutorial 2nd edn (Philadelphia: SIAM). doi:10.1137/1.9780898719505',
    'Ruge J W and Stuben K 1987 Algebraic multigrid in McCormick S F (ed) Multigrid Methods (Philadelphia: SIAM) 73-130. doi:10.1137/1.9781611971057.ch4',
    "Bernaschi M, Celestini A, Richelli G and D'Ambra P 2026 On the energy efficiency of sparse matrix computations on multi-GPU clusters Future Generation Computer Systems 183 108519. doi:10.1016/j.future.2026.108519",
    'Welter A and Nguyen N C 2026 Preconditioning techniques for hybridizable discontinuous Galerkin discretizations on GPU architectures Computer Methods in Applied Mechanics and Engineering 456 118951. doi:10.1016/j.cma.2026.118951',
    'Yuan F, Yang X, Huang Y, Dong D, Xu C, Liu J et al 2025 CRAMG: a communication-reduced algebraic multigrid method Proc. 39th ACM International Conference on Supercomputing 397-411. doi:10.1145/3721145.3725764',
    'Green D, Hu X, Lore J, Mu L and Stowell M L 2022 An efficient high-order numerical solver for diffusion equations with strong anisotropy Computer Physics Communications 276 108333. doi:10.1016/j.cpc.2022.108333',
    "Koskela T, Christidi I, Giordano M, Dubrovska E, Quinn J, Maynard C et al 2023 Principles for automated and reproducible benchmarking Proc. SC '23 Workshops 609-618. doi:10.1145/3624062.3624133",
    'Standard Performance Evaluation Corporation 2021 734.hpgmgfv_m: SPEChpc 2021 Benchmark Description. https://www.spec.org/hpc2021/docs/benchmarks/734.hpgmgfv_m.html accessed 8 September 2026',
    'Lawrence Livermore National Laboratory n.d. AMG2023: ATS-6 Benchmarks documentation. https://software.llnl.gov/benchmarks/10_amg/amg.html accessed 8 September 2026',
    'NVIDIA Corporation 2026 CUDA C++ Programming Guide. https://docs.nvidia.com/cuda/cuda-c-programming-guide/ accessed 3 September 2026',
    'NVIDIA Corporation 2026 Numba-CUDA Documentation. https://nvidia.github.io/numba-cuda/ accessed 3 September 2026',
    'Pekkila J, Lappi O, Robertsen F and Korpi-Lagg M J 2025 Stencil computations on AMD and Nvidia graphics processors: performance and tuning strategies Concurrency and Computation: Practice and Experience 37 e70129. doi:10.1002/cpe.70129',
    'Makhmut Y, Imankulov T, Gorlatch S and Matkerim B 2026 A CUDA performance study of global- and shared-memory kernels for the Buckley-Leverett polymer-flooding problem Applied Sciences 16 5449. doi:10.3390/app16115449',
    'Aksoylu B, Graham I G, Klie H and Scheichl R 2008 Towards a rigorously justified algebraic preconditioner for high-contrast diffusion problems Computing and Visualization in Science 11 319-331. doi:10.1007/s00791-008-0105-1',
    'Aksoylu B and Yeter Z 2009 Robust multigrid preconditioners for cell-centered finite volume discretization of the high-contrast diffusion equation arXiv:0904.1885 (preprint). doi:10.48550/arXiv.0904.1885',
    'Carson E, Liesen J and Strakos Z 2024 Towards understanding CG and GMRES through examples Linear Algebra and its Applications 692 241-291. doi:10.1016/j.laa.2024.04.003',
    'Firmbach M, Phillips M, Glusa C, Popp A, Siefert C M and Mayr M 2026 Smoothed aggregation algebraic multigrid for problems with heterogeneous and anisotropic materials arXiv:2602.05686 (preprint). doi:10.48550/arXiv.2602.05686',
    'Ewald R 2011 Automatic Algorithm Selection for Complex Simulation Problems PhD thesis University of Rostock. urn:nbn:de:gbv:28-diss2011-0162-1',
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
    doc = Document(TEMPLATE)
    props = doc.core_properties
    now = datetime.now(timezone.utc)
    props.author = "Dong Liu"
    props.last_modified_by = "Dong Liu"
    props.created = now
    props.modified = now
    props.title = "A Coefficient-Aware Finite-Difference Benchmark for Solver Selection and CPU/GPU Stencil Scaling in Heat-Conduction Simulation"
    props.subject = "ICEMCE 2026 reproducible heat-conduction benchmark"
    props.keywords = "heat conduction; finite difference; sparse solvers; algebraic multigrid; CPU/GPU stencil scaling; reproducible benchmark"
    clear_body(doc)
    set_document_defaults(doc)

    title_style = style_name(doc, "IOP-CS-Title")
    author_style = style_name(doc, "IOP-CS-Author")
    aff_style = style_name(doc, "IOP-CS-Affiliation")
    abstract_style = style_name(doc, "IOP-CS-Abstract", aff_style)
    body_first = style_name(doc, "IOP-CS-BodyNoIndent")
    body = style_name(doc, "IOP-CS-BodyText")
    ref_style = style_name(doc, "IOP-CS-ReferenceText")

    add_paragraph(
        doc,
        "A Coefficient-Aware Finite-Difference Benchmark for Solver Selection and CPU/GPU Stencil Scaling in Heat-Conduction Simulation",
        title_style,
        WD_ALIGN_PARAGRAPH.CENTER,
    )
    add_paragraph(doc, "Dong Liu*", author_style, WD_ALIGN_PARAGRAPH.CENTER)
    add_paragraph(doc, "University of Nottingham Ningbo China, Ningbo 315100, China", aff_style, WD_ALIGN_PARAGRAPH.CENTER)
    add_paragraph(doc, "*E-mail: ssydl3@nottingham.edu.cn", aff_style, WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_paragraph()

    add_paragraph(
        doc,
        'Abstract. Sparse solves for variable-coefficient heat conduction depend on coefficient geometry, forcing, preconditioner setup, and implementation. We present a verified finite-difference benchmark with an invariant-preserving audit of solver-choice claims. Smooth manufactured solutions recover second-order convergence and an aligned interface test verifies flux treatment. Beyond a baseline coefficient-family comparison, matched binary fields hold contrast, material fraction, total variation, and maximum log-gradient fixed. In a controlled N = 192, contrast-1000 case, translating the same two-island field by one grid point raises Jacobi-PCG iterations from 403 to 677 and reverses the setup-inclusive winner from Jacobi to AMG in all five repeats. Reflection-invariant Krylov subspaces explain why an odd source can avoid slow island modes; source perturbations and an independent motif family test this interpretation. An interleaved audit with classical AMG confirms that reversal locations depend on the candidate solver set. All 2956 controlled extension solves satisfy an independently checked relative residual below 1e-8. The resulting audit exposes limits of translation-invariant coefficient descriptors without proposing a new solver-selection algorithm. CPU/CUDA measurements separately quantify stencil scaling; GPU claims remain restricted to resident-data kernels. Raw CSV files, scripts, tests, and generated outputs support the numerical and performance claims.',
        abstract_style,
    )
    doc.add_paragraph()

    add_section(doc, 1, "Introduction")
    add_paragraph(
        doc,
        "Discretising heat conduction with spatially varying conductivity produces sparse linear systems whose solution cost depends on the coefficient field, mesh resolution, forcing and preconditioning. Repeated stencil evaluations introduce a separate implementation cost. A useful benchmark must verify the discretisation and specify which parts of these computations are timed.",
        body_first,
    )
    add_paragraph(
        doc,
        'We test whether coefficient summaries and grid resolution distinguish the measured solver choices. Matched coefficient fields, translations and source perturbations provide controlled tests of their limitations.',
        body,
    )
    add_paragraph(
        doc,
        "The benchmark solves the steady heat-conduction equation with spatially varying conductivity. Manufactured solutions verify the smooth cases; inclusion, layered and checkerboard fields test the solvers with discontinuous conductivity. The implementation uses Python, NumPy, SciPy, PyAMG, Numba, and Numba-CUDA for sparse solves and CPU/GPU stencil implementations [[1-4]]. ",
        body,
    )
    add_paragraph(
        doc,
        "Prior numerical-analysis texts establish the convergence properties of finite-difference discretisations and the role of Krylov and multigrid methods in sparse PDE solves [[5-9]]. Recent sparse and PDE solver studies further underline that preconditioning, sparse matrix execution, and accelerator mapping remain active constraints for modern workloads [[10-11]]; recent AMG and diffusion-solver work targets communication cost and coefficient difficulty more directly [[12-13]]. General reproducible-benchmarking work provides principles for automated reruns and evidence retention [[14]]. Here, numerical verification, coefficient descriptors and archived timings connect solver choices to the tested PDE and implementation. Combining PDE verification with performance benchmarking is established practice.",
        body,
    )
    add_paragraph(
        doc,
        'The contribution is a controlled audit within an existing finite-difference benchmark. Numerical verification and baseline solver/stencil measurements establish the implementation. An exact matched-field construction then tests whether standard coefficient descriptors distinguish solver difficulty. Translation controls preserve shape and topology as well as scalar descriptors, while forcing and transpose controls separate source symmetry from matrix and implementation effects. The resulting counterexamples are connected to preconditioned spectra and setup-inclusive costs. The study introduces no new PDE, discretisation, Krylov method, AMG algorithm, or GPU kernel; coefficient-aware denotes an auditable interpretation of measured cases, not an online selection algorithm.',
        body,
    )

    add_section(doc, 2, "Related Work")
    add_paragraph(doc, 'The closest benchmark precedents already combine elliptic problems and solver performance. HPGMG-FV solves variable-coefficient elliptic problems on Cartesian grids and supports CPU and accelerator execution [[15]]. AMG2023 benchmarks finite-difference diffusion with BoomerAMG and Krylov methods; its performance denominator includes setup time plus a specified number of solves [[16]]. Setup-inclusive timing is therefore an established practice. The present study addresses a narrower question through a small coefficient-family grid, explicit interface checks, and a complete record of measured solver choices. These systems provide methodological context; no performance comparison against HPGMG or hypre is claimed.', body_first)
    add_paragraph(
        doc,
        "Finite-difference methods provide a direct route from elliptic and parabolic PDEs to sparse linear systems on structured grids [[5]]. For self-adjoint diffusion operators, conservative flux forms are especially useful because face-based coefficient averaging preserves the symmetry and locality expected by Krylov methods. Once discretised, the main computational problem is sparse linear algebra rather than pointwise equation evaluation.",
        body_first,
    )
    add_paragraph(
        doc,
        "The conjugate-gradient method remains a baseline solver for symmetric positive definite systems [[6-7]]. Its performance depends strongly on spectral conditioning, which generally deteriorates under mesh refinement and can be strongly affected by coefficient contrast and geometry. Multigrid methods reduce this sensitivity by addressing error components across scales [[8]]. Algebraic multigrid extends that idea to matrix-defined problems without requiring a hand-built geometric hierarchy [[9]]. In this study, PyAMG is used as an accessible Python implementation of algebraic multigrid [[4]].",
        body,
    )
    add_paragraph(
        doc,
        "Performance portability is a separate concern. NumPy provides high-level array operations, SciPy provides sparse linear algebra, and Numba compiles numerical Python kernels to machine code [[1-3]]. CUDA exposes massively parallel GPU execution, but launch overhead and data movement can erase speedups on small problems [[17-18]]. Recent stencil and CUDA kernel studies report sensitivity to memory traffic, kernel structure, and problem size [[19-20]]. The benchmark therefore reports GPU results as resident-data kernel measurements for repeated updates where data stay on the device, and it keeps raw evidence for independent reruns [[14]].",
        body,
    )

    add_paragraph(doc, 'High-contrast preconditioning and isolated-island modes already have analytical foundations [[21-22]]. Krylov convergence depends on the spectral distribution and its excitation by the initial residual, so a condition number alone can be misleading [[23]]. Recent material-aware smoothed aggregation explicitly targets heterogeneous interfaces [[24]]. More generally, algorithm-selection studies recognise performance variation among instances with identical features [[25]]. Our extension applies these established ideas to an exact matched-field and translation audit, quantifying their consequences for verified heat-conduction solves and setup-inclusive choices. Neither source dependence nor feature insufficiency is claimed as a new general theorem.', body)

    add_section(doc, 3, "Mathematical Model and Discretisation")
    add_paragraph(
        doc,
        "The model problem is the steady heat-conduction equation with homogeneous Dirichlet boundary conditions unless otherwise stated. The coefficient k(x, y) represents spatially varying thermal conductivity.",
        body_first,
    )
    add_equation(doc, "−∇·(k(x,y)∇u(x,y)) = f(x,y),  (x,y) ∈ (0,1)²", 1)
    add_paragraph(
        doc,
        "The smooth test uses a sinusoidal variable coefficient, while the high-contrast stress test uses a circular inclusion. These two cases are deliberately synthetic: they remove geometry and data-acquisition uncertainty so that the numerical mechanisms can be measured cleanly.",
        body,
    )
    add_equation(doc, "k(x,y) = 1 + 0.5 sin(2πx) sin(2πy)", 2)
    add_equation(doc, "k(x,y) = 1 + 99 χ_D(x,y),  D = { (x,y) : (x−0.5)² + (y−0.5)² < 0.15² }", 3)
    add_paragraph(
        doc,
        "For the decision-map study, this pair is expanded into a parameterised coefficient grid. The smooth family uses k = 1 + a sin(2πx) sin(2πy) with a = (Cₖ - 1)/(Cₖ + 1), giving target contrast Cₖ. The inclusion, layered, and checkerboard families use piecewise values in {1, Cₖ} with Cₖ in {10, 30, 100}, while the smooth family uses Cₖ in {3, 10, 30} and the constant case gives Ck = 1. The layered field changes at y = 1/2; the checkerboard uses eight blocks per coordinate direction. The circle has radius 0.15 and centre (1/2, 1/2).",
        body,
    )
    add_paragraph(
        doc,
        "To report contrast, coefficient sharpness, and coefficient geometry separately, each coefficient field is summarised by Cₖ, the maximum nodal Euclidean magnitude of the log-gradient (centred interior and first-order one-sided boundary differences), and a grid-normalised total-variation proxy. In Equation (4), Δₓk and Δᵧk denote unscaled nearest-neighbour differences over all nodal pairs in each coordinate direction, and their absolute sums are divided by N−1. For discontinuous coefficient fields, the log-gradient descriptor depends on grid spacing and is interpreted at fixed N rather than as a continuous invariant. Small-grid spectral evidence is also recorded through computed condition-number estimates κ(A) = λₘₐₓ(A) / λₘᵢₙ(A).",
        body,
    )
    add_equation(doc, "Cₖ = max(k)/min(k),  Gₖ(h) = ||∇h log(k)||∞,  Vₖ = (Σ|Δₓk| + Σ|Δᵧk|)/(N−1)", 4)
    add_paragraph(
        doc,
        "The domain is discretised on an N by N uniform grid with spacing h = 1/(N - 1). Interior unknowns are ordered lexicographically. For an interior node (i, j), the conservative five-point stencil is assembled by face-based arithmetic averaging of adjacent conductivity values in the main two-dimensional decision map. Arithmetic averaging defines the primary two-dimensional benchmark operator; harmonic averaging probes sensitivity to the interface treatment. For discontinuous coefficient fields, harmonic face averaging is also implemented and tested as a sensitivity check because it matches the series-resistance interpretation of one-dimensional layered conduction. The shared positive face weights give a sum of weighted squared nodal differences in the discrete energy. With boundary values fixed, both choices produce sparse symmetric positive definite systems for positive k and homogeneous Dirichlet boundaries.",
        body,
    )
    add_equation(
        doc,
        "(Au)ᵢⱼ = h⁻²[kᵢ₊₁/₂,ⱼ(uᵢⱼ-uᵢ₊₁,ⱼ)+... ]",
        5,
    )
    add_paragraph(
        doc,
        "For smooth convergence verification, the exact solution is chosen in closed form and f is generated analytically for the constant and smooth coefficient cases. Errors are reported as the interior-node root-mean-square (normalised discrete L2) and maximum norms. The observed convergence rate is obtained by a least-squares fit of log(error) against log(h). A separate one-dimensional verification problem uses k(x) = k1 for x < 1/2 and k(x) = k2 for x > 1/2 with u(0) = 0 and u(1) = 1. Its analytic solution is piecewise linear and satisfies continuity of both u and k ux at the interface; this test isolates whether arithmetic and harmonic face averages respect the expected interface flux.",
        body,
    )
    add_equation(doc, "u_exact(x,y) = sin(πx) sin(πy)", 6)

    add_section(doc, 4, "Solver and Implementation Methods")
    add_paragraph(
        doc,
        "The assembled sparse matrix is solved with three methods: unpreconditioned CG, Jacobi-preconditioned CG, and algebraic-multigrid preconditioned CG. The AMG case uses the tested PyAMG default smoothed-aggregation hierarchy as a V-cycle preconditioner for SciPy CG; this should be read as one concrete AMG configuration rather than a claim about all AMG parameter choices. The recorded PyAMG 5.3.0 defaults use symmetric strength, standard aggregation, Jacobi prolongation smoothing with omega = 4/3, symmetric block Gauss-Seidel pre/post smoothing, at most ten levels, and a coarse-grid limit of ten unknowns. Historical runs did not fix the random starts used in PyAMG spectral-radius estimation, so exact hierarchy-dependent results can vary across reruns. Manufactured-solution runs use a relative residual tolerance of 1e-11 so that solver error does not dominate discretisation error; solver-comparison runs use SciPy CG with relative tolerance 1e-8, zero absolute tolerance, the default zero initial guess, and a maximum of 12000 iterations in the decision map. The baseline coefficient-family solver comparisons use the same deterministic unit right-hand side at a given grid size, so the right-hand side is controlled across cases. The controlled extension below separately varies the right-hand side, which can excite different spectral components. The reported time separates preconditioner setup from iterative solve time and also gives the total time. Matrix assembly and right-hand-side construction are excluded from these times. Iterative solve times include a callback that recomputes the true relative residual after every iteration, adding one sparse matrix-vector product and norm evaluations per iteration. The reported selections and speedups therefore apply to this monitored implementation. Methods are run in a fixed order, and the first AMG setup in a fresh process also includes the PyAMG import; these timings do not isolate hierarchy construction from first-use overhead. BLAS thread settings and processor power states were not recorded, limiting exact performance replication. Failed convergence would be recorded as a structured row in the raw CSV artefact, although all baseline benchmark cases converged.",
        body_first,
    )
    add_paragraph(
        doc,
        "Matrix-free performance is measured with a separate stencil apply matching Equation (5). Three CPU paths are compared: NumPy vectorisation, Numba serial compilation, and Numba parallel compilation with controlled thread counts. Throughput is reported as an estimated stencil bandwidth using a fixed byte model: 11 double-precision values per interior point for the variable-coefficient stencil, or 88 bytes per point. The Jacobi crossover uses five double-precision values per interior point, or 40 bytes per point. These estimates are operational metrics for comparing implementations of the same stencil family, not hardware peak-bandwidth or direct DRAM-transaction claims.",
        body,
    )
    add_paragraph(
        doc,
        "The CUDA experiment uses a repeated Jacobi update rather than the full variable-coefficient operator. This isolates a simple memory-bound stencil and avoids conflating kernel throughput with sparse-solver algorithmics. CPU and GPU arrays are allocated once, one batch is used for warm-up, and timing continues for at least three batches and 0.2 s. CUDA uses 16 by 16 thread blocks and the Numba CPU baseline uses four threads. These are within-run averages, not independent timing replicates. CUDA timings use a host wall-clock timer around resident-data batches of 20 updates, including Python launch overhead and device synchronisation after each batch. Allocation, compilation warm-up, and host-device transfers are excluded. This boundary matches repeated time-stepping or smoother-like updates where data remain resident on the device, but it should not be read as end-to-end application speedup.",
        body,
    )
    add_paragraph(
        doc,
        "For a single solve, the decision map compares setup-plus-solve times retrospectively: all candidates have already been run, and the winning time excludes evaluation of the other candidates. It selects the fastest converged solver by setup-plus-solve time, making one-time AMG setup cost visible rather than treating iteration count as the only outcome. It is not a repeated-right-hand-side reuse model; such a model would require an explicit solve count m. We report Spearman rank correlations between Ck, Gk(h), Vk, the available-grid condition estimate, CG iterations, and the speedup of the selected solver over CG. The coefficient set is a designed benchmark grid rather than a random sample from a defined population, so rank correlations are treated as descriptive association diagnostics rather than population-level inferential estimates. Pooled rows summarise all case-size entries but are not treated as independent samples because the same coefficient family appears at multiple grid sizes. Fixed-N rows provide the safer coefficient-level reading and include deterministic case-resampling intervals. Iteration-count associations are treated as the primary solver-difficulty diagnostic; associations with selected-solver speedup are secondary and exploratory because the full decision grid uses a single timing pass per cell. Permutation p-values are archived in the CSV as diagnostics rather than used to claim pairwise descriptor separation.",
        body,
    )
    add_equation(doc, "s*(c,N) = argmin_s [T_setup(s,c,N) + T_solve(s,c,N)]", 7)
    add_paragraph(
        doc,
        "Timing stability is assessed by repeating selected decision-map cases five times and then reporting the solver chosen by median total time, the per-repeat vote fraction, and the relative interquartile range of the selected method. The full decision grid remains a single-pass benchmark, while the repeat check probes whether the most important decisions are robust or near ties.",
        body,
    )
    add_paragraph(
        doc,
        "The hardware crossover model is similarly bounded: for the repeated Jacobi kernel it fits T(n) = α + βn, where n = (N - 2)², and archives the global four-point fit as an exploratory summary rather than a validated local crossover model.",
        body,
    )

    add_section(doc, 5, "Experiments and Results")
    add_paragraph(
        doc,
        "All experiments were run on Windows 11 with Python 3.12.9, NumPy 2.4.6, SciPy 1.18.1, Numba 0.67.0, PyAMG 5.3.0, and Numba-CUDA 0.30.4. The machine used an AMD Ryzen 9 7940HS w/ Radeon 780M Graphics CPU with 8 physical cores and 16 logical processors, approximately 16 GB of system memory reported by the operating system as 15.2 GB usable, and an NVIDIA GeForce RTX 4060 Laptop GPU with compute capability 8.9. The exact raw CSV outputs, environment metadata, and scripts are included in the supplementary artefact.",
        body_first,
    )
    add_paragraph(
        doc,
        "The decision map covers 13 coefficient cases, three grid sizes, and three Krylov/preconditioner choices. The spectral conditioning study uses N = 32, 64, and 128. Extremal eigenvalues of the unpreconditioned matrix are estimated with SciPy eigsh (smallest/largest algebraic eigenvalue, tolerance 1e-6, maximum 20000 iterations). These estimates do not describe the preconditioned operator; the N = 256 correlations using an N = 128 spectral proxy are cross-resolution diagnostics. The rank-correlation analysis uses all 39 case-size decisions and three fixed-grid strata of 13 cases; condition numbers are matched to N = 64 and N = 128 where available, and the N = 128 condition estimate is used as the maximum-available case-level spectral proxy for N = 256. The repeated timing check uses five repeats for one constant case and four nonconstant representative cases at each of the three decision-grid sizes, covering 15 case-size cells. The face-averaging sensitivity study reruns the three discontinuous Ck = 100 stress cases with arithmetic and harmonic face averages at N = 64, 128, and 256. The hardware crossover fit used the measured Jacobi-kernel timings at N = 512, 1024, 2048, and 4096.",
        body,
    )
    add_subsection(doc, "5.1", "Verification and Coefficient Difficulty")
    add_paragraph(
        doc,
        "The manufactured-solution study confirms the expected second-order behaviour of the finite-difference scheme. Table 1 reports fitted rates using N = 32, 64, 128, and 256 with a CG residual tolerance of 1e-11. Both the constant and smooth variable-coefficient cases produced L2 rates close to two. Figure 1 gives the same result as a log-log error plot.",
        body_first,
    )
    add_data_table(
        doc,
        "Table 1. Manufactured-solution convergence for the finite-difference discretisation.",
        ["Case", "p_L2", "p_inf", "Finest L2", "Residual"],
        convergence_table_rows(),
    )
    add_figure(
        doc,
        "convergence_l2.png",
        "Figure 1. Manufactured-solution convergence of the finite-difference operator.",
    )
    add_paragraph(
        doc,
        "The discontinuous-interface check in Table 2 isolates a different error mechanism. For an aligned one-dimensional two-material conduction problem, harmonic face averaging reproduced the analytic interface flux to roundoff, while arithmetic averaging showed a grid-refined interface error. This does not make harmonic averaging a universal choice for all multidimensional discontinuities, but it prevents the benchmark from relying only on smooth manufactured-solution evidence.",
        body,
    )
    add_data_table(
        doc,
        "Table 2. Discontinuous-interface verification on a one-dimensional two-material heat-conduction problem. Harmonic face averaging recovers the analytic flux continuity to roundoff in this aligned-interface test.",
        ["N", "L2 arithmetic", "L2 harmonic", "Flux err. arithmetic", "Flux err. harmonic"],
        interface_verification_rows(),
    )
    add_paragraph(
        doc,
        "Table 3 reports representative coefficient descriptors. The spectral evidence confirms that contrast alone is not a complete difficulty measure. At N = 128, the inclusion case with Ck = 100 had a computed condition-number estimate of 6.43e5, while the checkerboard case with the same contrast had a much smaller estimate of 3.12e4 under this discretisation. Figure 2 shows the same effect across the measured coefficient grid.",
        body,
    )
    add_data_table(
        doc,
        "Table 3. Representative coefficient-difficulty descriptors. Metrics use N = 64 for the discrete descriptors; kappa(A) is the largest available spectral estimate, here N = 128.",
        ["Case", "Family", "Ck", "Gk(h)", "TV proxy", "kappa(A)"],
        coefficient_difficulty_rows(),
    )
    add_figure(
        doc,
        "conditioning.png",
        "Figure 2. Computed condition-number response to coefficient contrast and coefficient geometry.",
    )
    add_paragraph(doc, 'The supplementary rank-correlation table distinguishes pooled size effects from fixed-grid coefficient comparisons. The matched condition estimate has pooled correlation 0.94 with selected-solver speedup, but fixed-grid samples contain only 13 cases and their case-resampling intervals overlap. These are descriptive ordering signals, not population confidence guarantees. The matched-field audit below tests descriptor sufficiency directly, rather than inferring it from pooled correlation.', body)


    add_subsection(doc, "5.2", "Solver Decision Map and Preconditioner Effect")
    add_paragraph(
        doc,
        "The single-pass setup-inclusive decision map records a resolution-dependent outcome. Within each grid size the winning class is the same across all tested coefficient fields, so this map supplies no evidence that descriptors improve prediction of the winner beyond resolution alone. Over the 13 coefficient cases, Jacobi-PCG was fastest in every N = 64 run, while AMG-PCG was fastest in every N = 128 and N = 256 run. Table 4 summarises this transition. The median speedup of the selected solver over CG increased from 2.79x at N = 64 to 7.80x at N = 256, and the largest speedup reached 25.72x for the layered Ck = 100 case. Because each decision-map cell uses one timing pass, this map is interpreted together with the repeated representative cases below.",
        body_first,
    )
    add_data_table(
        doc,
        "Table 4. Setup-inclusive single-solve decision summary over the coefficient-family grid. Counts report the fastest converged method by setup-plus-solve time from one timing pass per cell.",
        ["N", "Cases", "CG", "Jacobi-PCG", "AMG-PCG", "Median speedup", "Max speedup"],
        decision_summary_rows(),
    )
    add_paragraph(
        doc,
        "The supplementary face-averaging sensitivity table tests whether the discontinuous high-contrast solver conclusions are an artefact of arithmetic face averaging. Replacing arithmetic by harmonic averaging changed condition estimates and iteration counts, especially for checkerboard fields, but the fastest solver class was unchanged in all nine tested case-size cells: Jacobi-PCG remained fastest at N = 64, and AMG-PCG remained fastest at N = 128 and N = 256.",
        body,
    )
    add_paragraph(
        doc,
        'The supplementary timing-stability table reports all 15 case-size cells in the existing repeated-timing dataset. The median-best solver also won all five individual repeats in 14 cells: Jacobi-PCG for the four nonconstant N = 64 cases, and AMG-PCG for all five cases at both N = 128 and N = 256. The constant N = 64 cell is a near tie: the median favours Jacobi-PCG by only 1.03x, while CG wins four repeats. For constant conductivity on this uniform grid, the diagonal is a scalar multiple of the identity; Jacobi therefore does not improve the spectral condition number and yields equivalent CG iterates in exact arithmetic. The archived single-pass CG and Jacobi-PCG iteration counts agree at all three sizes. Their small-grid timing difference is not evidence of an iteration-reduction benefit.',
        body,
    )
    add_paragraph(
        doc,
        "Solver behaviour changed substantially when the coefficient field became high contrast. At N = 256, unpreconditioned CG required 4370 iterations in the high-contrast case, compared with 770 iterations in the smooth case. Jacobi preconditioning reduced the high-contrast iteration count to 535, while AMG-PCG reduced it to 12. Total time fell from 6.155 s for CG to 0.288 s for AMG-PCG in the high-contrast case. Table 5 summarises the finest-grid comparison, and Figure 3 shows total-time scaling across grid sizes. The iteration-scaling figure is retained in the supplementary artefact.",
        body,
    )
    add_data_table(
        doc,
        "Table 5. Solver comparison at N = 256 grid points in each direction.",
        ["Case", "Method", "Iter.", "Time (s)", "Rel. residual"],
        solver_table_rows(),
    )
    add_figure(
        doc,
        "solver_runtime.png",
        "Figure 3. Total setup plus solve time for CG, Jacobi-PCG, and AMG-PCG.",
    )


    add_subsection(doc, "5.3", "Matched-Field and Forcing Audit")
    add_paragraph(doc, 'Matched fields. Two 2-by-8 binary motifs contain 12 high cells and 20 high/low boundary edges but have one and two connected components, respectively. Integer dilation by s = N/16 and low-conductivity padding embed each motif in the unit square. The high phase has k = c and the background k = 1. For the tested grids, both fields have 12s² high nodes, mean 1 + (c - 1)12s²/N², total variation (c - 1)20s/(N - 1), and maximum log-gradient √2 (N - 1) log(c)/2. These counting identities are checked after embedding. A one-node translation preserves these quantities, component sizes, shape, and topology; it changes position relative to the source and boundary. Matching these invariants does not isolate topology as the sole cause of a performance difference.', body)
    add_figure(doc, "counterfactual_audit.png", 'Figure 4. Matched coefficient motifs and the forcing/translation audit. Bars show median setup-plus-solve times; whiskers span five runs. Iteration counts are annotated. The fields share scalar coefficient descriptors, while a rigid translation also preserves shape and connectivity.', width_inches=6.15)
    add_paragraph(doc, 'Controlled protocol. Following an exploratory 576-solve screen, confirmation uses c = 1000 and N = 96, 128, 192; centered, jointly transposed, and one-node x-shifted configurations; arithmetic and harmonic faces; and four unit-norm sources: constant, sin(2 pi x)sin(pi y), sin(pi x)sin(2 pi y), and a fixed-seed Gaussian vector. Jacobi-PCG and default SA-PCG each use five fresh setups per case, paired recorded setup seeds, shuffled method/source order, warm imports, and one BLAS thread. SA uses symmetric strength with theta = 0 and retains hierarchy diagnostics (keep=True). Count-only callbacks avoid the baseline residual-monitor overhead. CG uses rtol = 1e-9, zero initial guess, and at most 8000 iterations; an independent true relative residual must be at most 1e-8. Assembly and source construction are shared and excluded. The two timing protocols are not pooled.', body)
    add_paragraph(doc, 'A separate 3-by-6 motif family samples four connected and four disconnected patterns before observing their solver outcomes, retaining 12 occupied cells and 20 interface edges. It supplies 640 solves at N = 128, 192. This is a balanced constructed family, not a random sample of engineering materials. An additional 132-solve perturbation study varies translation direction and source admixtures with three repeats. The 1440 confirmation, 640 independent-family, and 132 perturbation solves all pass the true-residual check; the largest residual is below 3e-9. The pilot archive retains 84 failed acceptance checks, mainly at higher contrast or the CG iteration limit. No failed pilot timing is relabelled as a successful solve.', body)
    add_paragraph(doc, 'Mechanism. Let R reflect interior nodes in x and let D be the diagonal of A. If RA = AR, then R also commutes with D and the symmetrically scaled matrix S. For an odd source Rb = -b, every vector in the zero-start Krylov space generated by S and the scaled source g is odd. It is orthogonal to x-even eigenvectors in exact arithmetic. The centered two-island field satisfies this identity; its two slowest Jacobi-scaled modes are x-even. At N = 64 and c = 10000, computed squared source overlaps are below 1e-30 for both face averages. A transpose of both operator and source preserves Jacobi iteration counts, whereas translating the field in x breaks the reflection identity. This is a standard invariant-subspace explanation, not new convergence theory.', body)
    add_equation(doc, 'S = D^(-1/2) A D^(-1/2), g = D^(-1/2)b, Rb = -b', 8)
    add_paragraph(doc, 'Figure 4 shows a concrete decision consequence at N = 192 with harmonic faces and c = 1000. For the odd-x source, the centered two-island field takes 403 Jacobi iterations and 72.2 ms, versus 17 AMG-PCG iterations and 101.0 ms. A one-node x translation increases Jacobi to 677 iterations and 125.1 ms, while AMG-PCG takes 16 iterations and 97.5 ms. Each winner is unchanged across the five repeats. With the same centered operator but a random source, Jacobi takes 949 iterations and 166.2 ms, and AMG-PCG takes 15 iterations and 94.3 ms. These are measured medians on this workstation, not universal crossover thresholds.', body)
    add_paragraph(doc, 'The full confirmation has a consistent per-repeat winner in 124 of 144 cells; the independent motif family has 55 of 64. Only two of the 48 centered-versus-x-shifted pairs reverse their winner consistently in all five repeats, so the reversal is a counterexample rather than a population-frequency claim. For the odd-x example within the Jacobi/SA portfolio, any deterministic rule restricted to the preserved coefficient invariants must choose the same method for both positions. Let T(j,s) be the median setup-plus-solve time for position j and candidate s in portfolio P. The least excess cost of a fixed choice across the equally weighted pair is E(P), defined below. For the two-method example, 1 + E(P) = 1.142. This empirical floor is not a statistical lower confidence bound, a bound for other solver portfolios, or a proposed selector. The raw tables include all pairs, unstable cells, and both methods.', body)
    add_equation(doc, 'E(P) = min_s [1/2 sum_j T(j,s)/min_t T(j,t)] - 1', 9)

    add_paragraph(doc, 'Source perturbations test the interpretation without changing A: at N = 192, adding a constant component of amplitude 1e-8 to the unit odd source raises Jacobi from 403 to 569 iterations under the same stopping tolerance. A y translation preserves x reflection but can change the remaining spectrum and other symmetry sectors; parity alone is therefore not a complete runtime predictor. Offline spectra use symmetric Jacobi scaling and the nonsymmetric operator BA for the AMG inverse preconditioner B. Small-grid dense symmetrisation checks validate the numerical spectral procedure. Neither eigenvalue computations nor the reflection audit is included in a claimed low-cost selection policy.', body)

    add_paragraph(doc, 'Candidate-solver sensitivity. A separate 240-solve screen adds SA with symmetric-strength theta = 0.25 and classical Ruge-Stueben AMG with classical strength theta = 0.25. A subsequent 504-solve confirmation compares Jacobi, SA with theta = 0, and classical AMG at N = 128, 160, 192, using the two-island motif and the previously tested symmetric 3-by-6 anchor, whose three rows are each 110011. Each of seven repeats interleaves both field positions, both sources, both motifs, and all three methods at a fixed N. All 744 solves pass the same residual acceptance check; their timings are not pooled with earlier stages. The confirmation has 17 of 24 cells with the same winner in every repeat, and three of 12 translated pairs reverse their winner in all seven repeats. Table 6 reports all 12 pairs, including unstable cells and zero floors. For the original motif at N = 128 with odd-x forcing, centered Jacobi and classical AMG take 24.3 and 36.8 ms; after translation they take 42.3 and 34.2 ms. Jacobi iterations rise from 266 to 450, while classical AMG takes 11 in both positions. The three-method empirical excess-cost floor for this pair is 11.91%. At N = 192, classical AMG has the lowest median time at both positions, giving zero median-based floor for that pair, although the centered winner is not identical in all repeats. Thus translation sensitivity survives a stronger baseline, but its measured decision boundary and cost consequence depend on the candidate solver set.', body)

    add_data_table(doc, 'Table 6. All 12 translated pairs in the interleaved confirmation. Winners use median total time: J = Jacobi-PCG, RS = classical AMG-PCG; SA was also a candidate. Stable means both positions retain their respective winner in all seven repeats. E(P) uses measured medians even for unstable pairs; it is not a confidence bound.',
                   ["N", "Motif", "Source", "Centered", "Shifted", "Stable", "E(P) (%)"], portfolio_table_rows())

    add_subsection(doc, "5.4", "CPU and CUDA Stencil Scaling")
    add_paragraph(
        doc,
        "At N = 2048, NumPy required 0.1813 s per apply, while Numba serial required 0.005325 s and Numba parallel with four threads required 0.003725 s. Increasing thread count beyond four did not improve the largest case in this run; the measurements alone do not distinguish memory-system limits from scheduling overhead.",
        body_first,
    )
    add_paragraph(
        doc,
        "The CUDA Jacobi benchmark measures the resident-data update cost. At N = 512, GPU and CPU kernel times were essentially equal. At N = 1024, CUDA reached 1.52x speedup. At N = 2048 and N = 4096, the speedups increased to 3.23x and 3.51x, respectively. The measurements describe this kernel and workstation. They do not imply the same speedup for an end-to-end sparse solver.",
        body,
    )
    add_data_table(
        doc,
        "Table 7. Representative stencil-throughput measurements. CPU entries use the variable-coefficient operator at N = 2048; CUDA entries are kernel-only Jacobi steps with arrays resident on the device.",
        ["Experiment", "Method", "N", "Time", "Throughput/speedup"],
        performance_table_rows(),
    )
    add_figure(
        doc,
        "cpu_scaling.png",
        "Figure 5. Estimated CPU stencil bandwidth for the variable-coefficient stencil apply.",
    )
    add_figure(
        doc,
        "gpu_crossover.png",
        "Figure 6. CUDA kernel-only speedup for repeated Jacobi updates relative to a four-thread Numba CPU baseline.",
    )
    add_paragraph(doc, 'The measured timings are approximately equal at N = 512, and CUDA is faster at N = 1024. The supplementary artefact retains the exploratory four-point linear fit. Its negative CPU-time prediction at the measured N = 512 point invalidates its use as a crossover-location estimate; no fitted hardware-selection threshold is claimed.', body)

    add_section(doc, 6, "Discussion")
    add_paragraph(
        doc,
        'The matched-field audit qualifies the baseline resolution-dependent decision map. The original monitored runs show the expected setup-versus-iteration trade-off, but their uniform winner at each resolution does not establish descriptor sufficiency. In the controlled extension, a rigid translation or a source perturbation changes the effective Krylov workload while retaining the listed coefficient invariants. The practical recommendation is to test forcing, alignment, and candidate-solver sensitivity before interpreting a coefficient-stratified timing map as a reusable decision rule. The classical-AMG check shows why a cost floor established for two methods must be recomputed when the portfolio changes. Symmetric sources can be physically appropriate; their fast solves should be reported as workload-specific evidence, not treated as an error or extrapolated to arbitrary forcing.',
        body_first,
    )
    add_paragraph(
        doc,
        "The coefficient descriptors are empirical summaries, not conditioning theory. Their uncertainty intervals overlap, and small fixed-grid strata do not establish a reliable ordering of predictive importance. Pooled correlations also reflect resolution; N = 256 uses an N = 128 condition estimate. Case-resampling intervals describe sensitivity to this constructed dataset, not population confidence or performance on unseen geometries.",
        body,
    )
    add_paragraph(
        doc,
        "The stencil measurements demonstrate implementation and size effects. Nonmonotone CPU scaling is consistent with bandwidth or scheduling limits, but no hardware counters separate these causes. CUDA timings include launch and final synchronisation with data resident on the device. They exclude transfer costs and full sparse solves; the four-point fit cannot validate a crossover threshold.",
        body,
    )
    add_paragraph(
        doc,
        "The scope is two-dimensional structured grids, synthetic coefficients and one workstation. Harmonic averaging does not resolve curved interfaces cutting grid cells. Industrial geometries, unstructured finite elements and transient multiphysics remain outside the evidence. The contribution is a reproducible audit of numerical correctness and conditional solver costs, not production solver robustness.",
        body,
    )

    add_section(doc, 7, "Reproducibility Artefact")
    add_paragraph(
        doc,
        'The supplementary artefact is archived at https://doi.org/10.5281/zenodo.22668106 and contains scripts, raw CSV files, generated outputs, metadata, and tests. Baseline measurements remain available at https://doi.org/10.5281/zenodo.22303525; the matched-field, forcing, perturbation, and portfolio measurements are included in the new archive under results/raw/counterfactual. The reproduction instructions distinguish historical monitored runs from the controlled count-only timing protocol and preserve pilot failures. Tests check flux-energy identities, equality of scalar descriptors, reflection invariance, and transpose equivalence in addition to the original numerical verification. CPU-only tests explicitly skip unavailable CUDA tests; a CUDA-required mode treats missing GPU support as an error. Timing reruns may differ with machine state. Recorded configurations document the measured runs, and the supplied CSV files regenerate the reported tables and figures.',
        body_first,
    )

    add_section(doc, 8, "Conclusion")
    add_paragraph(
        doc,
        'In the controlled heat-conduction tests, preserving scalar coefficient descriptors, shape and connectivity does not guarantee the same fastest solver: source and alignment changes can alter the measured setup-inclusive choice. The classical-AMG comparison shows that the reversal also depends on the candidate solver set. These findings support checking forcing, alignment and candidate solvers before reusing a coefficient-based decision map, alongside operator verification, complete setup timing and retention of failed solves. The CPU/CUDA experiments provide separate stencil measurements, with GPU results limited to resident data on the tested workstation. The study introduces no new numerical algorithm or universal selection rule.',
        body_first,
    )

    p = doc.add_paragraph(style=style_name(doc, "IOP-CS-SectionHead"))
    p.add_run("Acknowledgements")
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.keep_together = True
    normalize_runs(p)
    add_paragraph(
        doc,
        'The author used OpenAI GPT-5 for editorial assistance and DeepSeek V4 Pro through Claude Code for language polishing. OpenAI GPT-6 Astra assisted with experimental design, code implementation, numerical analysis and manuscript preparation. The author independently reviewed the controlled experiments, including their derivations, timing boundaries and failure cases, and takes responsibility for the code, results, references and final manuscript.',
        body_first,
    )

    p = doc.add_paragraph(style=style_name(doc, "IOP-CS-SectionHead"))
    p.add_run("References")
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.keep_together = True
    normalize_runs(p)
    for i, ref in enumerate(REFERENCES, start=1):
        p = doc.add_paragraph(style=ref_style)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.add_run(f"[{i}] {ref}")
        normalize_runs(p)
        for run in p.runs:
            run.font.size = Pt(9)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    normalize_docx_revision(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
