"""Pilot report for E3-QE/MACE active-learning runs: attempts, qualification, magnetism, cost.

Usage (plain python, no pytest/matsim install needed beyond ase-free parsing):

    python scripts/e3_qe_pilot_report.py RUN_DIR [RUN_DIR ...] [--out DIR] [--nodes-per-job N]

Each RUN_DIR is one material's ``E3_QE_RUN_DIR`` (contains ``e3-qe-policy.json`` and
``iteration_NNNN/{state.json,dft/<candidate>/{pw.in,pw.out,label-metadata.json}}``).
Writes ``e3-qe-pilot-report.json`` and ``e3-qe-pilot-report.md`` to ``--out``
(default: the first RUN_DIR). Per (material, round) it records:

* attempted vs successful QE labels (successful = converged pw.x, label usable),
* numerical-qualification failures by class (scf_not_converged, timeout, no_output, ...),
* cost: summed per-label wall time and node-hours (wall x nodes per job),
* final magnetic moments (total / absolute, per-site when pw.out printed them),
* the DFT protocol tag (pbe vs pbe+u), Hubbard projector, SCF threshold, spin pattern.

Labels written before ``label-metadata.json`` existed are re-derived from pw.out.
Loose-SCF labels are *pilot-only*: the report lists the SCF threshold so they are
never mistaken for production-qualified labels. PBE and PBE+U are never merged.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any

_TOTAL_MAG = re.compile(r"total magnetization\s*=\s*(-?\d+\.\d+)\s*Bohr mag/cell")
_ABS_MAG = re.compile(r"absolute magnetization\s*=\s*(-?\d+\.\d+)\s*Bohr mag/cell")
_SITE_MAG = re.compile(r"atom:\s*(\d+)\s+charge:\s*(-?\d+\.\d+)\s+magn:\s*(-?\d+\.\d+)")
LOOSE_CONV_THR_RY = 1e-6  # above this the label is pilot-only, not production-qualified


def pw_wall_seconds(text: str) -> float | None:
    """Wall time from the final ``PWSCF : ... CPU ... WALL`` line (as e3_qe_timing_report)."""
    m = re.findall(r"PWSCF\s*:.*?CPU\s+(.*?)\s+WALL", text)
    if not m:
        return None
    parts = {u: float(v) for v, u in re.findall(r"([\d.]+)\s*([dhms])", m[-1])}
    return (
        parts.get("d", 0) * 86400
        + parts.get("h", 0) * 3600
        + parts.get("m", 0) * 60
        + parts.get("s", 0)
    )


def parse_magnetization(text: str) -> dict[str, Any] | None:
    """Same contract as matsim_agents.backends.dft.qe.parse_magnetization (inner dict)."""
    total, absolute = _TOTAL_MAG.findall(text), _ABS_MAG.findall(text)
    if not total and not absolute:
        return None
    out: dict[str, Any] = {}
    if total:
        out["total_magnetization"] = float(total[-1])
    if absolute:
        out["absolute_magnetization"] = float(absolute[-1])
    start = text.rfind("Magnetic moment per site")
    if start >= 0:
        sites = []
        for line in text[start:].splitlines()[1:]:
            m = _SITE_MAG.search(line)
            if m is None:
                if sites:
                    break
                continue
            sites.append({"atom": int(m[1]), "charge": float(m[2]), "magn": float(m[3])})
        if sites:
            out["per_site"] = sites
    return out


def classify_label(label_dir: Path) -> dict[str, Any]:
    """One label's record: metadata JSON when present, else re-derived from pw.out."""
    meta_path = label_dir / "label-metadata.json"
    meta: dict[str, Any] = json.loads(meta_path.read_text()) if meta_path.is_file() else {}
    out_path = label_dir / "pw.out"
    text = out_path.read_text(errors="replace") if out_path.is_file() else ""
    rec: dict[str, Any] = {"job_id": label_dir.name, "from_metadata": bool(meta)}
    if "converged" in meta:
        rec["converged"] = bool(meta["converged"])
        rec["failure_reason"] = meta.get("failure_reason")
    else:
        done = "JOB DONE." in text
        if done and "convergence NOT achieved" not in text:
            rec["converged"], rec["failure_reason"] = True, None
        elif "convergence NOT achieved" in text:
            rec["converged"], rec["failure_reason"] = False, "scf_not_converged"
        elif not text:
            rec["converged"], rec["failure_reason"] = False, "no_output"
        else:  # truncated output without JOB DONE.: most likely killed at the timeout
            rec["converged"], rec["failure_reason"] = False, "timeout_or_killed"
    wall = meta.get("wall_time_sec")
    rec["wall_sec"] = float(wall) if wall is not None else pw_wall_seconds(text)
    rec["n_atoms"] = meta.get("n_atoms")
    rec["protocol_tag"] = meta.get("dft_protocol_tag")
    mag = (meta.get("magnetization") or parse_magnetization(text)) if text or meta else None
    rec["magnetization"] = mag
    rec["spin_configuration"] = (meta.get("spin_configuration") or {}).get("name")
    return rec


def _stats(values: list[float]) -> dict[str, float] | None:
    return (
        {"min": min(values), "mean": statistics.fmean(values), "max": max(values)}
        if values
        else None
    )


def summarise_round(
    it_dir: Path, nodes_per_job: float, policy_tag: str | None
) -> dict[str, Any] | None:
    dft_dir = it_dir / "dft"
    if not dft_dir.is_dir():
        return None
    labels = [
        classify_label(d)
        for d in sorted(dft_dir.iterdir())
        if d.is_dir() and ((d / "pw.in").is_file() or (d / "pw.out").is_file())
    ]
    state_path = it_dir / "state.json"
    state = json.loads(state_path.read_text()) if state_path.is_file() else {}
    ok = [r for r in labels if r["converged"]]
    failures: dict[str, int] = {}
    for r in labels:
        if not r["converged"]:
            key = r["failure_reason"] or "other"
            failures[key] = failures.get(key, 0) + 1
    walls = [r["wall_sec"] for r in labels if r["wall_sec"] is not None]
    wall_total = sum(walls)
    tags = sorted({r["protocol_tag"] or policy_tag or "unknown" for r in labels})
    total_m = [
        r["magnetization"]["total_magnetization"]
        for r in ok
        if r["magnetization"] and "total_magnetization" in r["magnetization"]
    ]
    abs_m = [
        r["magnetization"]["absolute_magnetization"]
        for r in ok
        if r["magnetization"] and "absolute_magnetization" in r["magnetization"]
    ]
    return {
        "round": it_dir.name,
        "attempted": len(labels),
        "selected_in_state": state.get("n_selected"),
        "successful": len(ok),
        "failed": len(labels) - len(ok),
        "failure_reasons": failures,
        "protocol_tags": tags,
        "wall_sec_total": wall_total,
        "wall_sec_median": statistics.median(walls) if walls else None,
        "wall_sec_max": max(walls) if walls else None,
        "node_hours": wall_total * nodes_per_job / 3600.0,
        "dft_stage_wall_sec": (state.get("timings_sec") or {}).get("dft"),
        "magnetization_labels": len(total_m),
        "total_magnetization": _stats(total_m),
        "absolute_magnetization": _stats(abs_m),
        "labels": labels,
    }


def summarise_run(run_dir: Path, nodes_per_job: float | None = None) -> dict[str, Any]:
    pol_path = run_dir / "e3-qe-policy.json"
    policy = json.loads(pol_path.read_text()) if pol_path.is_file() else {}
    qe_cfg = ((policy.get("al_config") or {}).get("dft") or {}).get("qe") or {}
    dft_pool = (((policy.get("al_config") or {}).get("resources") or {}).get("pools") or {}).get(
        "dft"
    ) or {}
    npj = nodes_per_job if nodes_per_job is not None else float(dft_pool.get("nodes_per_job", 1))
    proto = policy.get("dft_protocol") or {}
    hubbard = policy.get("hubbard") or {}
    tag = proto.get("tag") or ("pbe+u" if hubbard.get("u_eV") else "pbe" if policy else None)
    rounds = [
        r
        for it in sorted(run_dir.glob("iteration_*"))
        if (r := summarise_round(it, npj, tag)) is not None
    ]
    conv_thr = (qe_cfg.get("extra_electrons") or {}).get("conv_thr")
    material = policy.get("material") or run_dir.name
    all_tags = sorted({t for r in rounds for t in r["protocol_tags"]})
    warnings = []
    if len(all_tags) > 1:
        warnings.append(f"MIXED DFT protocols in one run: {all_tags}; do not pool these labels")
    if isinstance(conv_thr, (int, float)) and conv_thr > LOOSE_CONV_THR_RY:
        warnings.append(
            f"loose SCF threshold conv_thr={conv_thr:g} Ry: pilot-only labels, "
            "not production-qualified (see label qualification)"
        )
    return {
        "material": material,
        "run_dir": str(run_dir),
        "policy": {
            "dft_protocol_tag": tag,
            "hubbard_u_eV": hubbard.get("u_eV") or None,
            "hubbard_projector": proto.get("hubbard_projector")
            if proto
            else (hubbard.get("projector") if hubbard.get("u_eV") else None),
            "spin_configuration": proto.get("spin_configuration"),
            "conv_thr_ry": conv_thr,
            "kpts": qe_cfg.get("kpts"),
            "extra_system": qe_cfg.get("extra_system"),
            "nodes_per_job": npj,
        },
        "warnings": warnings,
        "rounds": rounds,
        "totals": {
            "attempted": sum(r["attempted"] for r in rounds),
            "successful": sum(r["successful"] for r in rounds),
            "wall_sec_total": sum(r["wall_sec_total"] for r in rounds),
            "node_hours": sum(r["node_hours"] for r in rounds),
        },
    }


def _fmt_stats(s: dict[str, float] | None) -> str:
    return "-" if not s else f"{s['min']:.2f} / {s['mean']:.2f} / {s['max']:.2f}"


def render_markdown(runs: list[dict[str, Any]]) -> str:
    lines = ["# E3-QE pilot report", ""]
    for run in runs:
        pol = run["policy"]
        lines += [
            f"## {run['material']}",
            "",
            f"- DFT protocol: **{pol['dft_protocol_tag']}**"
            + (
                f" (U = {pol['hubbard_u_eV']} eV, projector `{pol['hubbard_projector']}`)"
                if pol["hubbard_u_eV"]
                else ""
            ),
            f"- SCF conv_thr: {pol['conv_thr_ry']} Ry; k-mesh: {pol['kpts']}; "
            f"nodes/job: {pol['nodes_per_job']:g}",
            f"- Spin pattern: {(pol['spin_configuration'] or {}).get('name', 'default (env starting_magnetization)')}",
        ]
        lines += [f"- WARNING: {w}" for w in run["warnings"]]
        lines += [
            "",
            "| Round | Attempted | Successful | Failed (by class) | Wall total (h) | Node-hours "
            "| Total mag (min/mean/max muB) | |Mag| (min/mean/max muB) |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for r in run["rounds"]:
            fails = ", ".join(f"{k}: {v}" for k, v in sorted(r["failure_reasons"].items())) or "-"
            lines.append(
                f"| {r['round']} | {r['attempted']} | {r['successful']} | {fails} "
                f"| {r['wall_sec_total'] / 3600:.2f} | {r['node_hours']:.2f} "
                f"| {_fmt_stats(r['total_magnetization'])} | {_fmt_stats(r['absolute_magnetization'])} |"
            )
        t = run["totals"]
        lines += [
            "",
            f"Total: {t['successful']}/{t['attempted']} labels successful, "
            f"{t['wall_sec_total'] / 3600:.2f} h label wall, {t['node_hours']:.2f} node-hours.",
            "",
        ]
    lines.append(
        "Successful = pw.x converged (JOB DONE., no 'convergence NOT achieved'). Loose-SCF pilot "
        "labels still need qualification against tighter references (energy and force errors) "
        "before production use. Failed labels are flagged, not accepted by widening gates."
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("run_dirs", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, help="output dir (default: first RUN_DIR)")
    ap.add_argument(
        "--nodes-per-job",
        type=float,
        help="override nodes per DFT job (default: policy resources.pools.dft.nodes_per_job or 1)",
    )
    args = ap.parse_args(argv)
    runs = [summarise_run(d, args.nodes_per_job) for d in args.run_dirs]
    out = args.out or args.run_dirs[0]
    out.mkdir(parents=True, exist_ok=True)
    (out / "e3-qe-pilot-report.json").write_text(json.dumps({"runs": runs}, indent=2))
    md = render_markdown(runs)
    (out / "e3-qe-pilot-report.md").write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
