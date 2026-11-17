"""Old (fixed mesh) vs new (constant density) validation labels: energy/force differences per material."""
import json
import numpy as np
from ase.io import read
I = "/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval/e3-qe-lux-inputs"
rows = {}
for m in ["lifepo4", "bcc_refractory", "fcc_cantor", "nb_ta_o", "phosphorene", "zn_formate_mof"]:
    old = read(f"{I}/validation-{m}.extxyz", index=":")
    new = read(f"{I}/validation-kdens/validation-{m}.extxyz", index=":")
    assert len(old) == len(new)
    dE, dF, ch, mesh = [], [], 0, {}
    for o, n in zip(old, new):
        assert np.allclose(o.positions, n.positions, atol=1e-6)
        if o.get_potential_energy() != n.get_potential_energy():
            ch += 1
            dE.append(abs(n.get_potential_energy() - o.get_potential_energy()) / len(o) * 1000)
            df = n.get_forces() - o.get_forces()
            dF.append((float(np.sqrt((df ** 2).mean())) * 1000, float(np.abs(df).max()) * 1000))
            mesh.setdefault(" ".join(map(str, np.atleast_1d(n.info["kpoint_mesh"]))), []).append(len(o))
    dE = np.array(dE); dF = np.array(dF)
    print(f"{m}: relabelled {ch}/{len(old)}  meshes {sorted(mesh)}")
    if ch:
        print(f"   |dE| meV/atom mean {dE.mean():.2f} max {dE.max():.2f} | force-diff RMS meV/A mean {dF[:,0].mean():.1f} max {dF[:,0].max():.1f}; max-component max {dF[:,1].max():.1f}")
