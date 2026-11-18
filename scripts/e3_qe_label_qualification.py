"""Qualify pilot QE labels against tighter references on a representative frame subset.

Subcommands:
  plan    pick frames from the validation sets, write run dirs + manifest.json (pw.in = original with SCF edits)
  task N  run entry N of the manifest (used by the sbatch array)
  report  parse every finished run, compare to the tightest converged reference per frame, write the markdown
"""
from __future__ import annotations

import csv
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path("/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval")
INP = ROOT / "e3-qe-lux-inputs"
QUAL = INP / "qualification"
PW_X = "/lustre/orion/ven136/proj-shared/qe/76omp-bf7acca2/bin/pw.x"
LAUNCHER = Path(__file__).resolve().parents[1] / "deployments/lux/launchers/_qe-step-lux.sh"
RY_EV = 13.605693122994
MATERIALS = ("phosphorene", "nb_ta_o", "zn_formate_mof", "bcc_refractory", "fcc_cantor", "lifepo4")
LIGHT = {"phosphorene", "nb_ta_o", "zn_formate_mof", "bcc_refractory"}


def set_electrons(text: str, edits: dict[str, str]) -> str:
    """Set/insert keys in the &ELECTRONS namelist of a pw.in."""
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.strip().upper().startswith("&ELECTRONS"))
    end = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == "/")
    block = lines[start + 1:end]
    for key, val in edits.items():
        pat = re.compile(rf"^\s*{re.escape(key)}\s*=", re.I)
        new = f"  {key} = {val}"
        for j, l in enumerate(block):
            if pat.match(l):
                block[j] = new
                break
        else:
            block.append(new)
    return "\n".join(lines[: start + 1] + block + lines[end:]) + "\n"


def frame_table() -> list[dict]:
    import numpy as np

    timing = {(r["material"], r["label"]): r for r in csv.DictReader(open(INP / "qe-timing.csv"))
              if r["kind"] == "validation"}
    rows = []
    for m in MATERIALS:
        for d in sorted((INP / "validation" / m / "frames").glob("f*")):
            t = timing.get((m, d.name))
            if t is None or not (d / "forces.npy").exists():
                continue
            f = np.load(d / "forces.npy")
            rows.append({"material": m, "label": d.name, "atoms": int(t["n_atoms"]),
                         "iters": int(t["scf_iterations"] or 0), "wall_min": float(t["wall_s"]) / 60,
                         "max_force": float(np.abs(f).max()), "dir": str(d)})
    return rows


def pick(rows: list[dict], material: str, atoms: set[int] | None = None) -> list[tuple[str, dict]]:
    g = [r for r in rows if r["material"] == material and (atoms is None or r["atoms"] in atoms)]
    chosen: dict[str, tuple[str, dict]] = {}

    def take(tag, r):
        if r["label"] not in chosen:
            chosen[r["label"]] = (tag, r)

    take("most-distorted", max(g, key=lambda r: r["max_force"]))
    take("hardest-scf", max(g, key=lambda r: (r["iters"], r["wall_min"])))
    med = statistics.median(r["wall_min"] for r in g)
    take("typical", min(g, key=lambda r: abs(r["wall_min"] - med)))
    return list(chosen.values())


def plan() -> None:
    rows = frame_table()
    runs: list[dict] = []

    def add(r, tag, name, edits, tier, cpu=False, note=""):
        d = QUAL / r["material"] / r["label"] / name
        d.mkdir(parents=True, exist_ok=True)
        orig = Path(r["dir"]) / "pw.in"
        (d / "pw.in").write_text(set_electrons(orig.read_text(), edits))
        runs.append({"material": r["material"], "frame": r["label"], "frame_tag": tag, "atoms": r["atoms"],
                     "name": name, "edits": edits, "tier": tier, "cpu": cpu, "note": note, "dir": str(d)})

    for m in MATERIALS:
        if m in LIGHT:
            for tag, r in pick(rows, m):
                add(r, tag, "ref-1e-10", {"conv_thr": "1.0d-10"}, "short")
        elif m == "lifepo4":
            small = pick(rows, m, {28})
            hardest = max((r for _, r in small), key=lambda r: (r["iters"], r["wall_min"]))
            for tag, r in small:
                for ct in ("5.0d-4", "1.0d-4", "2.0d-5", "1.0d-6"):
                    add(r, tag, f"ct{ct}", {"conv_thr": ct}, "short")
                add(r, tag, "cpu-1e-8", {"conv_thr": "1.0d-8"}, "long", cpu=True,
                    note="same pw.x, OMP_TARGET_OFFLOAD=DISABLED (host execution)")
                if r is hardest:
                    for nm, ed in (("beta0.1", {"mixing_beta": "0.1"}),
                                   ("localTF", {"mixing_mode": "'local-TF'"}),
                                   ("ppcg", {"diagonalization": "'ppcg'"}),
                                   ("fullacc", {"diago_full_acc": ".true."})):
                        add(r, tag, f"strat-{nm}-ct1e-6", {"conv_thr": "1.0d-6", **ed}, "short")
            big = min((r for r in rows if r["material"] == m and r["atoms"] == 112), key=lambda r: r["iters"])
            add(big, "112-atom-cheapest", "ct5.0d-4", {"conv_thr": "5.0d-4"}, "long")
        else:  # fcc_cantor
            sel = pick(rows, m)
            hardest = max((r for _, r in sel), key=lambda r: r["iters"])
            for tag, r in sel:
                for ct in ("1.0d-3", "2.0d-4", "5.0d-5"):
                    add(r, tag, f"ct{ct}", {"conv_thr": ct}, "long")
                if r is hardest:
                    add(r, tag, "strat-localTF-ct2.0d-4", {"conv_thr": "2.0d-4", "mixing_mode": "'local-TF'"}, "long")
    (QUAL).mkdir(parents=True, exist_ok=True)
    json.dump(runs, open(QUAL / "manifest.json", "w"), indent=1)
    print(len(runs), "runs;", sum(r["tier"] == "short" for r in runs), "short,", sum(r["tier"] == "long" for r in runs), "long")


def task(idx: int, tier: str) -> int:
    runs = [r for r in json.load(open(QUAL / "manifest.json")) if r["tier"] == tier]
    r = runs[idx]
    d = Path(r["dir"])
    if (d / "pw.out").exists() and "JOB DONE." in (d / "pw.out").read_text(errors="replace"):
        print("already done", d)
        return 0
    env = dict(os.environ, MATSIM_DEVICES_PER_NODE="8", MATSIM_NODE_DEVICES="8")
    ranks, threads = ("64", "2") if r["cpu"] else ("8", "16")
    if r["cpu"]:
        env["OMP_TARGET_OFFLOAD"] = "DISABLED"
    with open(d / "pw.out", "w") as log:
        subprocess.run(["bash", str(LAUNCHER), str(d), PW_X, str(d / "pw.in"), "1", ranks, threads],
                       stdout=log, stderr=subprocess.STDOUT, env=env, cwd=d)
    shutil.rmtree(d / "tmp", ignore_errors=True)
    for core in d.glob("core.*"):
        core.unlink()
    return 0


def wall(text: str):
    m = re.findall(r"PWSCF\s*:.*?CPU\s+(.*?)\s+WALL", text)
    if not m:
        return None
    p = {u: float(v) for v, u in re.findall(r"([\d.]+)\s*([dhms])", m[-1])}
    return p.get("d", 0) * 86400 + p.get("h", 0) * 3600 + p.get("m", 0) * 60 + p.get("s", 0)


def parse(out: Path) -> dict:
    import numpy as np
    from ase.io import read

    t = out.read_text(errors="replace") if out.exists() else ""
    res = {"done": "JOB DONE." in t, "converged": False, "iters": None, "acc_final": None, "acc_min": None,
           "wall_s": wall(t), "energy_eV": None, "forces": None, "tot_mag": None, "abs_mag": None, "sites": None}
    accs = [float(x) for x in re.findall(r"estimated scf accuracy\s*<\s*([\d.eE+-]+)", t)]
    if accs:
        res["acc_final"], res["acc_min"] = accs[-1], min(accs)
    m = re.search(r"convergence has been achieved in\s+(\d+)\s+iterations", t)
    if m:
        res["converged"], res["iters"] = True, int(m.group(1))
    elif "convergence NOT achieved" in t:
        res["iters"] = len(accs)
    tm = re.findall(r"total magnetization\s*=\s*([-\d.]+)", t)
    am = re.findall(r"absolute magnetization\s*=\s*([-\d.]+)", t)
    res["tot_mag"] = float(tm[-1]) if tm else None
    res["abs_mag"] = float(am[-1]) if am else None
    blocks = re.findall(r"Magnetic moment per site.*?\n((?:\s+atom:.*\n)+)", t)
    if blocks:
        res["sites"] = [float(re.search(r"magn:\s*([-\d.]+)", l).group(1)) for l in blocks[-1].splitlines()
                        if "magn:" in l]
    if res["converged"]:
        try:
            a = read(out, index=-1, format="espresso-out")
            res["energy_eV"] = float(a.get_potential_energy())
            res["forces"] = np.asarray(a.get_forces())
        except Exception as exc:  # noqa: BLE001
            res["parse_error"] = str(exc)
    return res


def report() -> None:
    import numpy as np
    from ase.io import read

    runs = json.load(open(QUAL / "manifest.json"))
    by_frame: dict[tuple, list[dict]] = {}
    for r in runs:
        r["res"] = parse(Path(r["dir"]) / "pw.out")
        by_frame.setdefault((r["material"], r["frame"]), []).append(r)
    summary = []
    for (m, f), g in by_frame.items():
        orig = parse(INP / "validation" / m / "frames" / f / "pw.out")
        atoms = g[0]["atoms"]
        cands = [r for r in g if r["res"]["energy_eV"] is not None and "strat-" not in r["name"]]
        # reference = converged run with the smallest conv_thr; CPU runs preferred when present
        def ct(r):
            return float(r["edits"]["conv_thr"].replace("d", "e"))
        ref = min(cands, key=lambda r: (not r["cpu"], ct(r))) if cands else None
        rows = [("pilot-label", orig, None)] + [(r["name"], r["res"], r) for r in g]
        for name, res, r in rows:
            row = {"material": m, "frame": f, "tag": g[0]["frame_tag"], "atoms": atoms, "run": name,
                   "cpu": bool(r and r["cpu"]), "converged": res["converged"], "iters": res["iters"],
                   "acc_final": res["acc_final"], "acc_min": res["acc_min"], "wall_h": (res["wall_s"] or 0) / 3600,
                   "tot_mag": res["tot_mag"], "abs_mag": res["abs_mag"], "ref": ref["name"] if ref else None}
            if ref and res["energy_eV"] is not None and res is not ref["res"]:
                dF = res["forces"] - ref["res"]["forces"]
                row["dE_meV_atom"] = (res["energy_eV"] - ref["res"]["energy_eV"]) / atoms * 1000
                row["dF_rms"] = float(np.sqrt((dF ** 2).mean()))
                row["dF_max"] = float(np.abs(dF).max())
            summary.append(row)
        sites = {"pilot-label": orig["sites"]}
        sites.update({r["name"]: r["res"]["sites"] for r in g if r["res"]["sites"]})
        summary[-1]["_sites"] = {k: v for k, v in sites.items() if v}
    json.dump(summary, open(QUAL / "summary.json", "w"), indent=1, default=str)
    print(len(summary), "rows written to", QUAL / "summary.json")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "plan":
        plan()
    elif cmd == "task":
        sys.exit(task(int(sys.argv[2]), sys.argv[3]))
    elif cmd == "report":
        report()
