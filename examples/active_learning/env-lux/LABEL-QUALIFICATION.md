# QE label qualification (pilot labels vs tighter references)

Scripts: `scripts/e3_qe_label_qualification.py` (plan/task/report), `scripts/sbatch_e3_qe_qualification.sh`, `scripts/sbatch_e3_qe_qualification_cpu.sh`.
Raw runs, manifest and `summary.json`: `e3-qe-lux-inputs/qualification/` (not committed). Same structure, cutoffs, k-mesh, pseudos and `mixing_beta` as the original label; only `&ELECTRONS` keys changed. Production configs untouched.
Build: `qe/develop_omp5_76omp-lux-tuned` (GPU, 1 node, 8 ranks x 16 threads). Cost: ~46 node-hours.
"Pilot" = the existing label. dE/dF are vs. the reference named in each table (tightest converged run).
Tolerances: energy gate 0.1 eV/atom = 100 meV/atom; force 0.02 eV/A (which quantity it applies to is still unconfirmed with Max, so both RMS and max are given).

## Frames and design

Per material: most-distorted (max |F|), hardest-SCF (most iterations), typical (median wall). Frames: phosphorene f0006/f0002/f0015; Nb-Ta-O f0012/f0016/f0005; Zn-formate MOF f0008/f0029/f0009; BCC refractory f0021/f0008/f0009; FCC Cantor f0021/f0010/f0000; LiFePO4 (28-atom, +U 5.3 eV on Fe-3d) f0019/f0024.
Substitutions: LiFePO4 112-atom is too expensive, so the ladder was run on the 28-atom frames and the 112-atom f0020 only got one tighter rerun. FCC Cantor 128-atom is the cheapest hard case; ladder stopped at what is reachable.

## Light materials (pilot conv_thr already ~1e-9 Ry)

Reference = rerun at conv_thr 1e-10. All 12 frames converged in both runs.

| material | frames | atoms | pilot acc (Ry) | dE (meV/atom) | dF rms (eV/A) | dF max (eV/A) | m (tot/abs) |
|---|---|---|---|---|---|---|---|
| phosphorene | 3 | 12-16 | 2e-9..5e-9 | <=0.01 | 2.5e-5..7e-5 | <=2e-4 | non-magnetic |
| Nb-Ta-O | 3 | 28 | 3e-9..6e-9 | <=0.005 | 1.1e-4..2.0e-4 | <=7.3e-4 | non-magnetic |
| Zn-formate MOF | 3 | 216 | 2e-9..6e-9 | 0.00 | 4.8e-5..1.1e-4 | <=6.9e-4 | non-magnetic |
| BCC refractory | 3 | 128 | 7e-9..9e-9 | <=0.001 | 6e-5..8e-5 | <=3.4e-4 | non-magnetic |

Verdict: **qualified** (forces 30x under 0.02 eV/A, energy 4+ orders under gate).

## LiFePO4 (+U, magnetic) and FCC Cantor (magnetic) - plateau, not convergence

| frame | atoms | run | converged | final est. acc (Ry) | dE vs ref (meV/atom) | dF rms / max (eV/A) | tot / abs mag (muB) | wall (h) |
|---|---|---|---|---|---|---|---|---|
| LFP f0019 (most distorted, hardest) | 28 | pilot (2e-3) | yes, 26 it | 7.7e-4 | 0.15 | 0.0127 / 0.077 | 16.00 / 16.06 | 0.19 |
| | | 5e-4 (ref) | yes, 27 it | 4.4e-4 | - | - | 16.00 / 16.05 | 0.20 |
| | | 1e-4, 2e-5, 1e-6 | no (150 it) | stalls 3e-4..2e-2 | - | - | 16.00 / 16.05 | ~1.05 |
| | | beta 0.1 / local-TF | no | 4.2e-4 / 1.5e-3 | - | - | 16.00 / 16.05 | ~1 |
| | | diago_full_acc | no | 1.5e-5 (best) | - | - | 16.00 / 16.03 | 1.3 |
| | | CPU pw.x 7.13 (1e-6) | no | min 3.2e-5, ends ~1e-1 | - | - | 16.00 / 16.03 | 1.8 |
| LFP f0024 (typical) | 28 | pilot / 5e-4 | yes, 14 it | 4.1e-4 | 0.00 | 0 / 0 | 16.00 / 16.05 | 0.15 |
| | | 1e-4..1e-6 | no | floor 2.3e-4 | - | - | 16.00 / 16.06 | ~1.04 |
| | | CPU pw.x 7.13 (1e-6) | no | min 8.4e-5 | - | - | 16.00 / 16.05 | 1.85 |
| LFP f0020 | 112 | pilot (2e-3) vs 5e-4 | both yes (30 / 78 it) | 1.6e-3 / 4.3e-4 | **6.22** | **0.081 / 0.295** | 64.00 / 64.2 | 1.6 / 2.9 |
| FCC f0021 (most distorted) | 128 | pilot (~4e-3 stop) | yes, 82 it | 4.0e-3 | **1.45** vs 1e-3 run | **0.110 / 0.420** | 54.6 / 110.1 | 0.93 |
| | | 1e-3 | yes, 158 it | 9.7e-4 | - | - | 55.2 / 116.7 | 1.5 |
| | | 2e-4, 5e-5 | no (300 it) | floor 6.4e-4 | - | - | 56.0 / 117.5 | 2.6 |
| FCC f0000 (typical) | 128 | pilot | yes, 101 it | 4.5e-3 | **1.20** vs 1e-3 run | **0.116 / 0.469** | 92.2 / 163.9 | 1.07 |
| | | 1e-3 | yes, 202 it | 9.7e-4 | - | - | 95.8 / 169.1 | 1.8 |
| | | 2e-4, 5e-5 | no | floor 6.5e-4 | - | - | 96.6 / 169.2 | 2.3 |
| FCC f0010 (hardest) | 128 | pilot | yes, 299 it | 4.8e-3 | no converged ref | - | 89.1 / 137.7 | 2.6 |
| | | 1e-3 / 2e-4 / 5e-5 / local-TF | no (300 it, local-TF timed out at 6 h) | 6.7e-3 / 4.3e-3 | - | - | 87-90 / 137-138 | 2.4 |

Notes:
- dE for every case is tiny against the 100 meV/atom gate (worst 6.2 meV/atom).
- **Force errors fail the 0.02 eV/A tolerance** where a reference exists: LFP f0019 (0.013 rms, 0.077 max), LFP-112 (0.081/0.295), FCC (0.11/0.42-0.47). FCC magnetization also shifts (total 54.6 -> 56.0, 92.2 -> 96.6) with tighter SCF, i.e. the pilot labels are not at a converged magnetic state.
- Failed alternatives: `ppcg` is removed in this QE ("not supported anymore (Dec. 2024)"); `david` is the default. GPU build with `OMP_TARGET_OFFLOAD=DISABLED` aborts (core dump), so it was not usable as a CPU path.

## GPU build vs CPU build

The CPU-only `qe/7.13.0-afar-23.2.1` pw.x (64 ranks x 2 threads, 1.8 h per frame) shows the same SCF floor on both 28-atom LFP frames (min 3e-5 / 8e-5 Ry, 150 iterations, not converged to 1e-6) and the same moments (16.00 / 16.03-16.05). The GPU omp-offload build therefore does **not** look responsible for the stall. The cause is the SCF problem itself (+U / magnetic smearing, gaussian degauss 3.7 mRy, mixing). Caveat: only conv_thr 1e-6 on two frames was run on CPU, and the CPU build is a different QE version (7.13 vs 8.0dev), so tiny numerical differences are not separated.

## Recommendation

1. Light, non-magnetic materials: keep the current settings.
2. Magnetic materials: pilot conv_thr (2e-3..4e-3 Ry) does not meet the 0.02 eV/A force tolerance. The accessible floor with `mixing_beta 0.3`, `david` is 3e-4 (LFP) and 6e-4..1e-3 (FCC). conv_thr 5e-4 (LFP) / 1e-3 (FCC) is reachable, ~2x the cost, and is the best qualification step so far; whether it reaches 0.02 eV/A was **not** shown (no reference tighter than that exists).
3. Next to try (not done): `diago_full_acc=.true.` (reached 1.5e-5 Ry on f0019, best of all strategies), smaller `degauss`/different smearing (marzari-vanderbilt), `mixing_ndim` 12-16, constrained starting magnetization / `tot_magnetization`, then a force comparison. A tighter reference on 28-atom LFP via full_acc is the cheapest way to settle the 0.02 criterion.
4. Do not treat these labels as qualified for magnetic LiFePO4 and FCC Cantor until a converged reference exists. Force tolerance semantics should be confirmed with Max.
