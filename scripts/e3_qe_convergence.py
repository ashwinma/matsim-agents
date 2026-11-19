"""Max's QE convergence checks: +20% cutoffs on one validation frame per material, and phosphorene vacuum.

Each task copies the original validation frame's pw.in (so every SCF override is identical), edits only
ecutwfc/ecutrho (x factor) or the c-axis length, and runs pw.x once on one Lux node via the Lux wrapper.
usage (inside a Lux allocation): e3_qe_convergence.py run --nodes N [--only task,task]
       e3_qe_convergence.py report
"""
from __future__ import annotations

import argparse, json, queue, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

INPUTS = Path("/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval/e3-qe-lux-inputs")
OUT = INPUTS / "convergence"
KBAR_PER_EV_A3 = 1602.1766
FACTOR = 1.2

# name: (material, validation frame, kind, parameter)
TASKS = {
    "lifepo4-112": ("lifepo4", "f0013", "cutoff", FACTOR),
    "fcc_cantor": ("fcc_cantor", "f0000", "cutoff", FACTOR),
    "fcc_cantor-control": ("fcc_cantor", "f0000", "cutoff", 1.0),
    "bcc_refractory": ("bcc_refractory", "f0026", "cutoff", FACTOR),
    "zn_formate_mof": ("zn_formate_mof", "f0015", "cutoff", FACTOR),
    "nb_ta_o": ("nb_ta_o", "f0008", "cutoff", FACTOR),
    "lifepo4-28": ("lifepo4", "f0029", "cutoff", FACTOR),
    "lifepo4-28-control": ("lifepo4", "f0029", "cutoff", 1.0),
    "phosphorene": ("phosphorene", "f0000", "cutoff", FACTOR),
    "phosphorene-c25": ("phosphorene", "f0000", "vacuum", 25.0),
    "phosphorene-c30": ("phosphorene", "f0000", "vacuum", 30.0),
    "phosphorene-c15": ("phosphorene", "f0000", "vacuum", 15.0),
}


def _scale_cutoffs(text: str, f: float) -> str:
    def sub(m):
        v = float(m.group(2).replace("d", "e")) * f
        return m.group(1) + f"{v:.8e}".replace("e", "d")
    return re.sub(r"(ecut(?:wfc|rho)\s*=\s*)([0-9.deE+-]+)", sub, text)


def _set_c(text: str, c: float) -> str:
    lines = text.split("\n")
    i = next(k for k, l in enumerate(lines) if l.startswith("CELL_PARAMETERS"))
    a1, a2, a3 = (list(map(float, lines[i + 1 + j].split())) for j in range(3))
    assert abs(a1[2]) < 1e-8 and abs(a2[2]) < 1e-8 and abs(a3[0]) < 1e-8 and abs(a3[1]) < 1e-8, "cell not c||z"
    lines[i + 3] = f"  {0.0:18.10f} {0.0:18.10f} {c:18.10f}"
    return "\n".join(lines)


def _parse(out: Path):
    from ase.io import read
    a = read(out, index=-1, format="espresso-out")
    r = a.calc.results
    text = out.read_text(errors="replace")
    return {"n_atoms": len(a), "energy_eV": float(r["energy"]), "forces": np.asarray(r["forces"]).tolist(),
            "stress_kbar": (np.asarray(r["stress"]) * KBAR_PER_EV_A3).tolist() if "stress" in r else None,
            "done": "JOB DONE." in text and "convergence NOT achieved" not in text}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "report"])
    ap.add_argument("--nodes", type=int, default=1)
    ap.add_argument("--only")
    ap.add_argument("--timeout-sec", type=int, default=14400)
    args = ap.parse_args()
    if args.cmd == "run":
        run(args)
    else:
        report()


def run(args):
    import os
    from matsim_agents.execution.placement import ResourcePlan
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from e3_qe_reference_inputs import load_dft, REPO
    dft = load_dft(REPO / "examples/active_learning/e3_qe_mace_lux.yaml")
    plan = ResourcePlan.from_mapping(
        {"resources": {"preset": "lux", "pools": {"dft": {"nodes": args.nodes, "devices": "all", "nodes_per_job": 1}}}},
        source="e3_qe_convergence")
    pool = plan.place().pool("dft")
    free = queue.Queue()
    for l in pool.launches:
        free.put(l)
    names = args.only.split(",") if args.only else list(TASKS)
    order = sorted(names, key=lambda n: TASKS[n][0] not in ("lifepo4", "fcc_cantor"))  # heavy first
    cfg = dft.qe

    def one(name):
        mat, frame, kind, p = TASKS[name]
        wd = OUT / name
        if (wd / "result.json").exists():
            return name
        src = INPUTS / "validation" / mat / "frames" / frame / "pw.in"
        text = src.read_text()
        text = _scale_cutoffs(text, p) if kind == "cutoff" else _set_c(text, p)
        wd.mkdir(parents=True, exist_ok=True)
        (wd / "pw.in").write_text(text)
        launch = free.get()
        try:
            argv = ["bash", str(cfg.pw_wrapper), str(wd), str(cfg.pw_bin), str(wd / "pw.in"), *launch.wrapper_args()]
            t = time.time()
            with open(wd / "pw.out", "w") as f:
                try:
                    subprocess.run(argv, cwd=wd, stdout=f, stderr=subprocess.STDOUT, timeout=args.timeout_sec,
                                   check=False, env=launch.environment())
                except subprocess.TimeoutExpired:
                    pass
            rec = {"task": name, "material": mat, "frame": frame, "kind": kind, "param": p, "wall_s": time.time() - t}
            try:
                rec.update(_parse(wd / "pw.out"))
            except Exception as exc:  # noqa: BLE001
                rec.update(done=False, error=str(exc))
            (wd / "result.json").write_text(json.dumps(rec))
            print(name, "done" if rec.get("done") else "FAILED", f"{rec['wall_s']:.0f}s", flush=True)
        finally:
            free.put(launch)
        return name

    with ThreadPoolExecutor(max_workers=len(pool.launches)) as ex:
        list(ex.map(one, order))


def _orig(mat, frame):
    return _parse(INPUTS / "validation" / mat / "frames" / frame / "pw.out")


def report():
    rows = []
    for name, (mat, frame, kind, p) in TASKS.items():
        f = OUT / name / "result.json"
        if not f.exists():
            rows.append({"task": name, "status": "missing"}); continue
        r = json.loads(f.read_text())
        o = _orig(mat, frame)
        n = r.get("n_atoms") or o["n_atoms"]
        row = {"task": name, "material": mat, "frame": frame, "atoms": n, "kind": kind, "param": p,
               "wall_h": r["wall_s"] / 3600, "done": r.get("done", False)}
        if r.get("done"):
            row["dE_meV_atom"] = (r["energy_eV"] - o["energy_eV"]) / n * 1000
            if kind == "cutoff":
                dF = np.abs(np.asarray(r["forces"]) - np.asarray(o["forces"]))
                row["max_dF"] = float(dF.max()); row["rms_dF"] = float(np.sqrt((dF ** 2).mean()))
                if r["stress_kbar"] and o["stress_kbar"]:
                    row["max_dStress_kbar"] = float(np.abs(np.asarray(r["stress_kbar"]) - np.asarray(o["stress_kbar"])).max())
        rows.append(row)
    (OUT / "summary.json").write_text(json.dumps(rows, indent=1))
    for r in rows:
        print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}))


if __name__ == "__main__":
    main()
