#!/usr/bin/env python
"""Build the E3-QE reference inputs on Lux: per-material elemental references and held-out validation sets.

Subcommands (run inside a Slurm allocation for the compute ones; the host
venv drives pw.x through deployments/lux/launchers/_qe-step-lux.sh):

  plan        write the declared elemental phase plans + structures (CPU only)
  elemental   run elemental_dft.prepare_elemental_references for one material
  validation  label deterministic held-out frames for one material with the
              material's exact DFT settings, then write extxyz + sidecar

The DFT settings are read from the material's AL yaml (env-lux/<material>.sh
sourced), so labels and references share one method signature by construction.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import queue
import sys
import threading
import time
from pathlib import Path

import numpy as np
import yaml
from ase import Atoms
from ase.build import bulk, molecule
from ase.io import read, write
from ase.spacegroup import crystal

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

MATERIAL_ELEMENTS = {
    "lifepo4": ["Fe", "Li", "O", "P"],
    "phosphorene": ["P"],
    "zn_formate_mof": ["C", "H", "O", "Zn"],
    "nb_ta_o": ["Nb", "O", "Ta"],
    "bcc_refractory": ["Hf", "Nb", "Ta", "Ti", "V", "Zr"],
    "fcc_cantor": ["Co", "Cr", "Fe", "Mn", "Ni"],
}
# Valence electrons (Zval) of the SSSP UPFs, read from the real UPF headers.
ZVAL = {"Co": 17, "Cr": 14, "Fe": 16, "Mn": 15, "Ni": 18, "O": 6}
STRESS_TOL = 0.01  # eV/A^3, the documented example tolerance
SEED_BASE = 20261116


def _kmesh(cell, target):
    return [max(1, math.ceil(target / float(x))) for x in cell.lengths()]


def _phase(pid, element, atoms, outdir, *, kind="bulk", target=30.0, mag=None, relax_cell=None,
           hubbard=None, kpts=None):
    path = outdir / f"{pid}.extxyz"
    write(path, atoms, format="extxyz")
    d = {
        "phase_id": pid,
        "element": element,
        "structure_path": path.name,
        "kind": kind,
        "geometry_status": "requires_relaxation",
        "relaxation_force_tolerance_eV_per_A": 0.02,
        "relaxation_max_steps": 200,
        "kpts": kpts if kpts is not None else _kmesh(atoms.cell, target),
        "hubbard_u": {} if hubbard is None else hubbard,
    }
    if kind == "bulk" and relax_cell is not False:
        d["relaxation_stress_tolerance_eV_per_A3"] = STRESS_TOL
    if relax_cell is False:
        d["relax_cell"] = False
    if mag is None:
        d["magnetic_state"] = "nonmagnetic"
        d["qe_magnetic_settings"] = {"nspin": 1}
    else:
        d["magnetic_state"] = mag["state"]
        d["qe_magnetic_settings"] = mag["qe"]
    return d


def _fm(element, mu):
    return {"state": f"ferromagnetic start, {mu} muB initial",
            "qe": {"nspin": 2, "starting_magnetization(1)": round(mu / ZVAL[element], 4)}}


def build_phases(outdir: Path) -> list[dict]:
    outdir.mkdir(parents=True, exist_ok=True)
    P = []
    for el, a in (("Nb", 3.30), ("Ta", 3.30), ("V", 3.03), ("Li", 3.51)):
        P.append(_phase(f"{el.lower()}-bcc", el, bulk(el, "bcc", a=a), outdir))
    for el, a, ca in (("Hf", 3.19, 1.58), ("Zr", 3.23, 1.593), ("Ti", 2.95, 1.587), ("Zn", 2.66, 1.856)):
        P.append(_phase(f"{el.lower()}-hcp", el, bulk(el, "hcp", a=a, c=a * ca), outdir))
    P.append(_phase("ni-fcc", "Ni", bulk("Ni", "fcc", a=3.52), outdir, mag=_fm("Ni", 0.6)))
    P.append(_phase("co-hcp", "Co", bulk("Co", "hcp", a=2.507, c=2.507 * 1.623), outdir, mag=_fm("Co", 3.0)))
    P.append(_phase("co-fcc", "Co", bulk("Co", "fcc", a=3.54), outdir, mag=_fm("Co", 3.0)))
    P.append(_phase("fe-bcc", "Fe", bulk("Fe", "bcc", a=2.866), outdir, mag=_fm("Fe", 3.0)))
    P.append(_phase("cr-bcc", "Cr", bulk("Cr", "bcc", a=2.88), outdir, mag=_fm("Cr", 3.0)))
    P.append(_phase("mn-bcc", "Mn", bulk("Mn", "bcc", a=2.91), outdir, mag=_fm("Mn", 3.0)))
    P.append(_phase("mn-fcc", "Mn", bulk("Mn", "fcc", a=3.60), outdir, mag=_fm("Mn", 3.0)))
    graphite = crystal(["C", "C"], [(0, 0, 0.25), (1 / 3, 2 / 3, 0.25)], spacegroup=194, cellpar=[2.46, 2.46, 6.71, 90, 90, 120], primitive_cell=True)
    P.append(_phase("c-graphite", "C", graphite, outdir, target=20.0))
    P.append(_phase("c-diamond", "C", bulk("C", "diamond", a=3.567), outdir, target=20.0))
    black_p = crystal("P", [(0, 0.10168, 0.08056)], spacegroup=64, cellpar=[3.3136, 10.478, 4.3763, 90, 90, 90])
    P.append(_phase("p-black", "P", black_p, outdir, target=20.0, relax_cell=False))
    for pid, el, name, mag in (("o2-triplet", "O", "O2", {"state": "triplet (tot_magnetization=2)",
                                "qe": {"nspin": 2, "tot_magnetization": 2, "starting_magnetization(1)": round(1.0 / ZVAL["O"], 4)}}),
                               ("h2-singlet", "H", "H2", None)):
        m = molecule(name)
        m.set_cell([15.0, 16.0, 17.0])
        m.center()
        m.pbc = True
        P.append(_phase(pid, el, m, outdir, kind="molecule", mag=mag, kpts=[1, 1, 1]))
    return P


def cmd_plan(args):
    out = Path(args.out) / "elemental"
    phases = build_phases(out / "structures")
    plan = {"protocol": "declared_phases_zero_pressure_v3", "phases": [
        {**p, "structure_path": f"structures/{p['structure_path']}"} for p in phases]}
    (out / "plan.yaml").write_text(yaml.safe_dump(plan, sort_keys=False))
    alt = [p for p in plan["phases"] if p["element"] == "Fe"]
    for p in alt:
        p["hubbard_u"] = {"Fe-3d": 5.3}
        p["phase_id"] += "-U"
    (out / "plan-lifepo4-fe-with-U.yaml").write_text(
        yaml.safe_dump({"protocol": plan["protocol"], "phases": [
            {**p} for p in plan["phases"] if p["element"] != "Fe"] + alt}, sort_keys=False))
    print(f"wrote {len(phases)} phases to {out}")


def load_dft(yaml_path: Path):
    from matsim_agents.backends.dft.config import DFTConfig
    from matsim_agents.execution.variables import expand_variables

    text = expand_variables(yaml_path.read_text(), {}, source=yaml_path)
    return DFTConfig.model_validate(yaml.safe_load(text)["dft"])


def placement_for(nodes: int, nodes_per_job: int):
    from matsim_agents.execution.placement import ResourcePlan

    plan = ResourcePlan.from_mapping(
        {"resources": {"preset": "lux", "pools": {"dft": {"nodes": nodes, "devices": "all", "nodes_per_job": nodes_per_job}}}},
        source="e3_qe_reference_inputs")
    return plan.place().pool("dft")


def cmd_elemental(args):
    from matsim_agents.active_learning.elemental_dft import ElementalReferencePlan, prepare_elemental_references

    dft = load_dft(Path(args.config))
    dft.qe.timeout_sec = args.timeout_sec
    pool = placement_for(args.nodes, args.nodes_per_job)
    root = Path(args.out) / "elemental"
    plan_file = root / ("plan-lifepo4-fe-with-U.yaml" if args.fe_with_u else "plan.yaml")
    name = args.material + ("-feU" if args.fe_with_u else "")
    manifest = prepare_elemental_references(
        ElementalReferencePlan.from_yaml(plan_file), dft, launch=pool.launches[0],
        required_elements=set(MATERIAL_ELEMENTS[args.material]),
        cache_dir=root / "cache" / name, output_dir=root / "manifests" / name,
        phases_approved=True, dft_approved=True, max_dft_calculations=args.max_calcs)
    print("MANIFEST", manifest)


def _base_structures(material: str):
    s = REPO / "research/paper/e4/aurora-dft-scaling/stage1-inputs-v2"
    seeds = REPO / "examples/paper_cases/seeds"
    if material == "bcc_refractory":
        return [read(p) for p in sorted((s / "bcc_refractory").glob("*/POSCAR"))]
    if material == "fcc_cantor":
        return [read(p) for p in sorted((s / "fcc_hea").glob("*/POSCAR"))]
    if material == "lifepo4":
        return [read(p) for p in sorted((s / "lifepo4").glob("*/POSCAR"))] + [read(seeds / "lifepo4_olivine.extxyz")]
    if material == "nb_ta_o":
        return [read(p) for p in sorted((REPO / "research/nb-ta-o/pilot/poscars").glob("*.POSCAR"))]
    if material == "phosphorene":
        b, u = read(seeds / "phosphorene_black_P.extxyz"), read(seeds / "phosphorene_blue_P.extxyz")
        return [b, u, b.repeat((2, 2, 1)), u.repeat((3, 2, 1))]
    if material == "zn_formate_mof":
        # COD 7205949 only: it is the pool the E3 pipeline uses and the only Zn-formate
        # seed with hydrogen (the alpha/beta extxyz seeds are C8O8Zn4, no H).
        return [read(seeds / "zn_formate_cod_7205949.cif")]
    raise ValueError(material)


def build_frames(material: str, n: int, only_small: int | None = None) -> list[Atoms]:
    bases = _base_structures(material)
    if only_small:
        bases = [b for b in bases if len(b) <= only_small]
    strains = [1.0, 0.99, 1.01]
    frames = []
    for i in range(n):
        base = bases[i % len(bases)]
        variant = i // len(bases)
        rng = np.random.default_rng(SEED_BASE + 1000 * list(MATERIAL_ELEMENTS).index(material) + i)
        a = base.copy()
        a.calc = None
        a.set_cell(a.cell * strains[variant % 3] ** (1 / 3), scale_atoms=True)
        a.positions += rng.normal(0.0, 0.04, a.positions.shape)
        a.pbc = True
        a.info = {"validation_base_index": i % len(bases), "validation_variant": variant,
                  "validation_seed": SEED_BASE + 1000 * list(MATERIAL_ELEMENTS).index(material) + i,
                  "material": material}
        frames.append(a)
    return frames


def cmd_validation(args):
    from ase.calculators.singlepoint import SinglePointCalculator
    from concurrent.futures import ThreadPoolExecutor
    from matsim_agents.active_learning.dft_protocol import dft_method_signature
    from matsim_agents.backends.dft.base import DFTJobSpec, make_backend
    from matsim_agents.datasets.governance import DatasetValidationSummary, write_dataset_manifest

    dft = load_dft(Path(args.config))
    dft.qe.timeout_sec = args.timeout_sec
    if args.extra_electrons:
        dft.qe.extra_electrons = {**dft.qe.extra_electrons, **json.loads(args.extra_electrons)}
    if args.extra_system:
        dft.qe.extra_system = {**dft.qe.extra_system, **json.loads(args.extra_system)}
    if args.hubbard_projector:
        dft.qe.hubbard_projector = args.hubbard_projector
    if args.hubbard_off:
        dft.qe.hubbard_u = None  # diagnostic only; never used for the delivered sets
    if (dft.qe.kpts is None) == (dft.qe.kpoint_spacing_inv_A is None):
        raise SystemExit("validation needs exactly one of dft.qe.kpts / kpoint_spacing_inv_A (source env-lux/kdensity.sh or set E3_QE_KPTS)")
    backend = make_backend(dft)
    pool = placement_for(args.nodes, args.nodes_per_job)
    frames = build_frames(args.material, args.n_frames, args.max_atoms)
    indices = [int(x) for x in args.only.split(",")] if args.only else list(range(len(frames)))
    root = Path(args.out) / "validation" / args.material
    (root / "frames").mkdir(parents=True, exist_ok=True)
    free = queue.Queue()
    for launch in pool.launches:
        free.put(launch)
    results = {}
    lock = threading.Lock()

    def run(i):
        wd = root / "frames" / f"f{i:04d}"
        done = wd / "result.json"
        if done.exists():
            return i, json.loads(done.read_text())
        launch = free.get()
        try:
            wd.mkdir(parents=True, exist_ok=True)
            write(wd / "input.extxyz", frames[i], format="extxyz")
            t = time.time()
            res = backend.run_one(DFTJobSpec(job_id=f"{args.material}-{i}", atoms=frames[i], work_dir=str(wd), launch=launch))
            rec = {"converged": bool(res.converged), "energy_eV": res.energy_eV, "wall": time.time() - t, "notes": res.notes,
                   "n_atoms": len(frames[i])}
            if res.converged:
                np.save(wd / "forces.npy", np.asarray(res.forces_eV_per_A))
                np.save(wd / "stress.npy", np.asarray(res.stress_eV_per_A3) if res.stress_eV_per_A3 is not None else np.zeros(0))
            done.write_text(json.dumps(rec))
            print(f"frame {i} converged={rec['converged']} E={rec['energy_eV']} wall={rec['wall']:.0f}s", flush=True)
            return i, rec
        finally:
            free.put(launch)

    with ThreadPoolExecutor(max_workers=len(pool.launches)) as ex:
        for i, rec in ex.map(run, indices):
            results[i] = rec
    good = [i for i in sorted(results) if results[i]["converged"]]
    out_frames = []
    for i in good:
        wd = root / "frames" / f"f{i:04d}"
        a = read(wd / "input.extxyz")
        f = np.load(wd / "forces.npy")
        s = np.load(wd / "stress.npy")
        a.info["energy"] = results[i]["energy_eV"]
        a.arrays["forces"] = f
        if s.size:
            a.info["stress"] = s
        a.info["dft_backend"] = "qe"
        a.info["source_work_dir"] = str(wd)
        if dft.qe.kpoint_spacing_inv_A is not None:
            from matsim_agents.backends.dft.qe_relax import kmesh_from_spacing
            a.info["kpoint_mesh"] = " ".join(map(str, kmesh_from_spacing(a.cell, dft.qe.kpoint_spacing_inv_A)))
            a.info["kpoint_spacing_inv_A"] = " ".join(map(str, dft.qe.kpoint_spacing_inv_A))
        else:
            a.info["kpoint_mesh"] = " ".join(map(str, dft.qe.kpts))
        out_frames.append(a)
    target = Path(args.out) / f"validation-{args.material}.extxyz"
    write(target, out_frames, format="extxyz")
    elements = set(MATERIAL_ELEMENTS[args.material])
    write_dataset_manifest(
        target, dft_backend="qe", energy_reference="qe:native_total_energy",
        validation=DatasetValidationSummary(accepted=len(out_frames)),
        method_signature=dft_method_signature(dft, elements), method_signature_elements=elements,
        base_method_signature=dft_method_signature(dft, set()),
        element_method_signatures={e: dft_method_signature(dft, {e}) for e in sorted(elements)},
        split_role="validation")
    print(f"WROTE {target} frames={len(out_frames)}/{len(frames)} failed={[i for i in results if not results[i]['converged']]}")
    return 0 if len(out_frames) == len(indices) else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=["plan", "elemental", "validation"])
    ap.add_argument("--out", default="/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval/e3-qe-lux-inputs")
    ap.add_argument("--material", choices=sorted(MATERIAL_ELEMENTS))
    ap.add_argument("--config", default=str(REPO / "examples/active_learning/e3_qe_mace_lux.yaml"))
    ap.add_argument("--nodes", type=int, default=1)
    ap.add_argument("--nodes-per-job", type=int, default=1)
    ap.add_argument("--n-frames", type=int, default=32)
    ap.add_argument("--max-atoms", type=int)
    ap.add_argument("--max-calcs", type=int)
    ap.add_argument("--timeout-sec", type=int, default=14400)
    ap.add_argument("--fe-with-u", action="store_true")
    ap.add_argument("--hubbard-off", action="store_true")
    ap.add_argument("--only", help="comma-separated frame indices (diagnostics / extra-parallel jobs)")
    ap.add_argument("--extra-system", help="JSON merged into dft.qe.extra_system (diagnostics)")
    ap.add_argument("--hubbard-projector")
    ap.add_argument("--extra-electrons", help="JSON merged into dft.qe.extra_electrons (diagnostics)")
    args = ap.parse_args()
    if args.cmd == "plan":
        return cmd_plan(args)
    if args.cmd == "elemental":
        return cmd_elemental(args)
    raise SystemExit(cmd_validation(args))


if __name__ == "__main__":
    main()
