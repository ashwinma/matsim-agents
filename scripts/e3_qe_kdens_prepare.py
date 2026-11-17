"""Seed a kdens run tree from the existing validation frames, copying only small result files.

Frames whose constant-density mesh equals the old fixed mesh keep their label (result.json is copied, so the
validation command skips them); frames whose mesh changes by >20% in total k-points are left without a result
and get relabelled. Every copied frame's stored input is checked against the deterministic build_frames() output.
"""
import json, math, shutil, sys
from pathlib import Path
import numpy as np
from ase.io import read

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src")); sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))
from e3_qe_reference_inputs import build_frames  # noqa: E402
from matsim_agents.backends.dft.qe_relax import kmesh_from_spacing  # noqa: E402

I = Path("/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval/e3-qe-lux-inputs")
OUT = I / "kdens-run"
plan = json.load(open(I / "kmesh-density-plan.json"))
SMALL = ("forces.npy", "stress.npy", "input.extxyz", "pw.in", "pw.out", "result.json")
summary = {}
for m, d in plan.items():
    frames = build_frames(m, 32, None)
    spacing, old = d["spacing_inv_A"], tuple(d["ref_mesh"])
    reused, relabel = [], []
    for i, a in enumerate(frames):
        src = I / "validation" / m / "frames" / f"f{i:04d}"
        stored = read(src / "input.extxyz")
        assert np.allclose(stored.positions, a.positions, atol=1e-6) and np.allclose(stored.cell.array, a.cell.array, atol=1e-6), (m, i)
        new = kmesh_from_spacing(a.cell, spacing)
        if abs(math.prod(new) / math.prod(old) - 1) > 0.2:
            relabel.append(i)
            continue
        dst = OUT / "validation" / m / "frames" / f"f{i:04d}"
        dst.mkdir(parents=True, exist_ok=True)
        for name in SMALL:
            if (src / name).exists():
                shutil.copy2(src / name, dst / name)
        reused.append(i)
    summary[m] = {"reused": len(reused), "relabel": relabel}
    print(m, "reused", len(reused), "relabel", relabel)
json.dump(summary, open(I / "kdens-prepare.json", "w"))
