"""Summarise the phosphorene k-mesh scan (scripts/sbatch_kmesh_phos_scan.sh): energy/atom and force deltas vs the densest spacing."""
import json, sys
from pathlib import Path
import numpy as np
from ase.io import read
OUT = Path("/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval/e3-qe-lux-inputs/kmesh-phosphorene")
tags = ["s0.272", "s0.2", "s0.15", "s0.1", "s0.07", "s0.05", "s0.035", "fixed7x5x1"]
ref = sys.argv[1] if len(sys.argv) > 1 else "s0.07"
D = {}
for t in tags:
    for fd in sorted((OUT / t / "validation/phosphorene/frames").glob("f*")):
        r = fd / "result.json"
        if not r.exists() or not json.load(open(r))["converged"]:
            continue
        j = json.load(open(r)); a = read(fd / "input.extxyz")
        pw = (fd / "pw.in").read_text().split("K_POINTS")[1].split("\n")[1].split()[:3]
        D[(t, int(fd.name[1:]))] = (j["energy_eV"] / len(a), np.load(fd / "forces.npy"), " ".join(pw), len(a), j["wall"])
frames = sorted({k[1] for k in D})
print(f"reference = {ref}; dE in meV/atom (E - E_ref), force RMS/max-component diff in meV/A")
print("frame natoms | " + " | ".join(tags))
for f in frames:
    row = []
    for t in tags:
        if (t, f) not in D or (ref, f) not in D: row.append("   n/a"); continue
        e, F, m, n, w = D[(t, f)]; e0, F0 = D[(ref, f)][:2]
        d = F - F0
        row.append(f"{m.replace(' ','x')} dE={1e3*(e-e0):+.2f} dF={1e3*np.sqrt((d**2).mean()):.1f}/{1e3*abs(d).max():.1f}")
    print(f"f{f:02d} n={D[next(k for k in D if k[1]==f)][3]} | " + " | ".join(row))
