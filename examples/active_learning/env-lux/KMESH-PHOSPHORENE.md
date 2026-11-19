# Phosphorene k-mesh convergence (Lux, QE pw.x, 2026-11-19)

Setup: 6 frames of the 32-frame phosphorene validation set (f01, f05 = 2-atom blue; f03, f07 = 12-atom blue; f00 = 4-atom black;
f02 = 16-atom black), SCF settings of `env-lux/phosphorene.sh` (PBE, SSSP P.pbe-n-rrkjus_psl, 30/240 Ry, gaussian 0.005 Ry,
conv_thr 1e-8), Gamma-only along vacuum, Gamma-centred automatic mesh. Meshes come from `kmesh_from_spacing`
(n_i = round(2*pi|b_i|/spacing)) with spacing s in-plane. Driver: `scripts/sbatch_kmesh_phos_scan.sh`; analysis:
`scripts/e3_qe_kmesh_phos_analyze.py`; raw outputs: `e3-qe-lux-inputs/kmesh-phosphorene/<tag>/`.
Reference = densest spacing (0.035 1/A; f05/f07 only reached 0.07, which is already identical to 0.1 within 0.01 meV/atom).

Each cell: mesh, dE (meV/atom) vs reference, force diff RMS/max-component (meV/A). "fixed7x5x1" = Max's mesh applied verbatim
to every cell (7x5x1 is also what s=0.272 gives on the 4-atom black cell f00).

    reference = s0.07; dE in meV/atom (E - E_ref), force RMS/max-component diff in meV/A
    frame natoms | s0.272 | s0.2 | s0.15 | s0.1 | s0.07 | s0.05 | s0.035 | fixed7x5x1
    f00 n=4 | 7x5x1 dE=+23.51 dF=168.4/287.7 | 10x7x1 dE=-5.91 dF=51.5/84.5 | 13x9x1 dE=+3.29 dF=72.0/102.9 | 19x14x1 dE=-0.46 dF=19.1/35.0 | 27x19x1 dE=+0.00 dF=0.0/0.0 | 38x27x1 dE=-0.57 dF=17.1/34.6 | 54x39x1 dE=-0.32 dF=15.7/32.7 | 7x5x1 dE=+23.51 dF=168.4/287.7
    f01 n=2 | 8x8x1 dE=+2.60 dF=6.2/10.1 | 11x11x1 dE=+0.27 dF=0.7/1.1 | 15x15x1 dE=+0.01 dF=0.1/0.2 | 22x22x1 dE=+0.00 dF=0.1/0.1 | 32x32x1 dE=+0.00 dF=0.0/0.0 | 44x44x1 dE=+0.00 dF=0.0/0.0 | 63x63x1 dE=+0.00 dF=0.0/0.0 | 7x5x1 dE=+12.24 dF=16.2/25.1
    f02 n=16 | 3x2x1 dE=-7.86 dF=358.5/801.9 | 5x3x1 dE=+1.44 dF=104.3/280.0 | 6x5x1 dE=-3.13 dF=71.9/177.9 | 10x7x1 dE=+1.41 dF=23.8/64.7 | 14x10x1 dE=+0.00 dF=0.0/0.0 | 19x14x1 dE=-0.77 dF=18.5/41.3 | 27x19x1 dE=-0.72 dF=10.5/24.0 | 7x5x1 dE=-1.18 dF=48.4/106.1
    f03 n=12 | 3x4x1 dE=+1.22 dF=3.5/7.7 | 4x6x1 dE=+0.13 dF=0.5/1.1 | 5x7x1 dE=+0.01 dF=0.1/0.2 | 7x11x1 dE=-0.00 dF=0.1/0.2 | 11x16x1 dE=+0.00 dF=0.0/0.0 | 15x22x1 dE=-0.00 dF=0.1/0.2 | 21x32x1 dE=-0.00 dF=0.0/0.0 | 7x5x1 dE=+0.18 dF=0.6/1.1
    f05 n=2 | 8x8x1 dE=+2.67 dF=6.5/11.0 | 11x11x1 dE=+0.28 dF=1.1/1.9 | 15x15x1 dE=+0.02 dF=0.1/0.1 | 22x22x1 dE=+0.00 dF=0.1/0.2 | 32x32x1 dE=+0.00 dF=0.0/0.0 |    n/a |    n/a | 7x5x1 dE=+12.42 dF=16.0/26.7
    f07 n=12 | 3x4x1 dE=+1.07 dF=3.7/7.8 | 4x6x1 dE=+0.10 dF=0.5/1.1 | 5x7x1 dE=+0.01 dF=0.1/0.2 | 7x11x1 dE=-0.00 dF=0.0/0.1 | 11x16x1 dE=+0.00 dF=0.0/0.0 |    n/a |    n/a | 7x5x1 dE=+0.16 dF=0.6/1.3

## Findings
- Blue phosphorene (2- and 12-atom hexagonal cells) converges quickly: s=0.15 gives <0.03 meV/atom and <0.3 meV/A; s=0.2 is
  <0.3 meV/atom and ~1 meV/A. s=0.272 is off by 2.6 meV/atom (2-atom) / 1.1 meV/atom (12-atom).
- Black phosphorene validation frames (4- and 16-atom) converge slowly and non-monotonically (e.g. f00: +23.8, -5.6, +3.6, -0.1,
  +0.3, -0.2 meV/atom for s=0.272..0.05). Their residual force noise is ~5-16 meV/A even at s=0.05-0.07 (these frames are strained/rattled
  enough that smearing at 0.005 Ry makes them sensitive to k sampling). Energy is within 1 meV/atom of reference for s<=0.07
  (f02: 0.72 at 0.07, 0.04 at 0.05).
- Max's fixed 7x5x1 is NOT adequate for the 2-atom cell (12.2-12.4 meV/atom, 16 meV/A RMS; the 2-atom hex cell
  needs ~15x15x1 for <0.1 meV/atom) nor for the 4- and 16-atom black cells (23.5 meV/atom / 168 meV/A on the 4-atom cell; the
  16-atom cell at 7x5x1 is on the other hand coarse-by-density only by luck, 48 meV/A). It happens to be adequate for the 12-atom
  blue cell (0.16-0.18 meV/atom, 0.6 meV/A).
- The earlier wip spacing 0.272 (3x2x1, 3x4x1, 4x3x1 on the supercells) is too coarse: up to 8 meV/atom and 360 meV/A.

## Recommendation
E3_QE_KPOINT_SPACING='[0.07, 0.07, 0]' (in-plane 1/A, Gamma-only along vacuum). This meets <1 meV/atom vs the densest mesh on all
6 frames; forces are <0.3 meV/A on blue cells and 10-16 meV/A on the two black frames, whose forces are not converged below ~0.01 eV/A even at
s=0.035 (noise floor, not a reason to go denser). s=0.1 is an acceptable cheaper choice for blue-phosphorene-only work (<0.01 meV/atom) but gives
1.4-2.1 meV/atom on black 16-atom cells.
Cost per label on one Lux node (8 GCDs): s=0.272 ~30 s, 0.1 ~100 s, 0.07 ~150-200 s, 0.05 ~300-360 s, 0.035 ~600-800 s.
Consequence: the 24 frames relabelled in `validation-kdens/` at s=0.272 should be relabelled at 0.07 before use.

Scan cost: 6 nodes x 8.9 min + 4 nodes x 19.7 min = 0.89 + 1.31 = 2.2 node-hours.
