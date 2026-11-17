"""Derive per-material constant-density k-spacings from Max's reference meshes and list affected validation frames."""
import csv, json, math, sys
from pathlib import Path
import numpy as np
from ase.io import read

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from matsim_agents.backends.dft.qe_relax import kmesh_from_spacing  # noqa: E402

I = Path("/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval/e3-qe-lux-inputs")
SEEDS = REPO / "examples/paper_cases/seeds"
POSCAR = REPO / "research/nb-ta-o/pilot/poscars/NbTaO5_ordering_01.POSCAR"

def frame_cell(material, natoms):
    # unstrained (variant 0 mod 3) frame, so the +-1 % strain variants do not bias the reference
    for f in sorted((I / "validation" / material / "frames").glob("f*/input.extxyz")):
        a = read(f)
        if len(a) == natoms and int(a.info.get("validation_variant", 0)) % 3 == 0:
            return a.cell
    raise SystemExit(f"no {natoms}-atom frame for {material}")

# reference cell + Max's mesh; axes with mesh 1 are Gamma-only (spacing 0)
REF = {
    "lifepo4": (lambda: frame_cell("lifepo4", 112), (2, 4, 8)),
    "bcc_refractory": (lambda: frame_cell("bcc_refractory", 128), (2, 2, 2)),
    "fcc_cantor": (lambda: frame_cell("fcc_cantor", 128), (2, 2, 2)),
    "nb_ta_o": (lambda: read(POSCAR).cell, (4, 8, 9)),
    "phosphorene": (lambda: read(SEEDS / "phosphorene_black_P.extxyz").cell, (7, 5, 1)),
    "zn_formate_mof": (lambda: read(SEEDS / "zn_formate_cod_7205949.cif").cell, (3, 2, 2)),
}

def spacings(cell, mesh):
    b = np.linalg.norm(np.asarray(cell.reciprocal()), axis=1)
    return [0.0 if n == 1 else round(2 * math.pi * x / n, 4) for x, n in zip(b, mesh)]

if __name__ == "__main__":
    wall = {}
    for r in csv.DictReader(open(I / "qe-timing.csv")):
        if r["kind"] == "validation":
            wall[(r["material"], r["label"])] = float(r["wall_s"])
    out = {}
    for m, (cellf, mesh) in REF.items():
        cell = cellf()
        sp = spacings(cell, mesh)
        repro = kmesh_from_spacing(cell, sp)
        frames = []
        for f in sorted((I / "validation" / m / "frames").glob("f*/input.extxyz")):
            a = read(f)
            new = kmesh_from_spacing(a.cell, sp)
            old = REF[m][1]
            frames.append({"frame": f.parent.name, "atoms": len(a), "old": old, "new": new,
                           "k_ratio": math.prod(new) / math.prod(old), "wall_s": wall.get((m, f.parent.name))})
        out[m] = {"spacing_inv_A": sp, "ref_mesh": mesh, "ref_cell_lengths": [round(x, 3) for x in cell.lengths()], "reproduces": list(repro) == list(mesh), "frames": frames}
    json.dump(out, open(I / "kmesh-density-plan.json", "w"), indent=1, default=list)
    for m, d in out.items():
        fr = d["frames"]
        changed = [x for x in fr if abs(x["k_ratio"] - 1) > 0.2]
        print(f"{m}: spacing={d['spacing_inv_A']} refcell={d['ref_cell_lengths']} reproduces={d['reproduces']} frames={len(fr)} changed>20%={len(changed)}")
        by = {}
        for x in fr:
            by.setdefault((x["atoms"], tuple(x["old"]), tuple(x["new"])), []).append(x)
        for (na, o, n), g in sorted(by.items()):
            w = sum(x["wall_s"] or 0 for x in g) / 3600
            print(f"    {len(g):2d} frames  {na:3d} atoms  old {o} -> new {n}  (k-points x{math.prod(n)/math.prod(o):.2f}, old wall {w:.1f} node-h)")
