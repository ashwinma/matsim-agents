"""Compare energy/forces (MAE, rms, max) of two QE pw.out files: python e3_qe_force_compare.py A.out B.out [label]."""
import sys, numpy as np
from ase.io import read
def F(p):
    a = read(p, index=-1, format="espresso-out"); return a.get_forces(), a.get_potential_energy(), len(a)
def cmp(a, b, label):
    fa, ea, n = F(a); fb, eb, _ = F(b); d = fa - fb
    print(f"{label}: dE {1000*(ea-eb)/n:.3f} meV/at  MAE {np.abs(d).mean():.4f}  rms {np.sqrt((d**2).mean()):.4f}  max {np.abs(d).max():.4f}  |F|max {np.abs(fb).max():.3f}")
if __name__ == "__main__":
    cmp(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
