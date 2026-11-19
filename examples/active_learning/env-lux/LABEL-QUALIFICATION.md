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

## Tight-reference attempt (round 2): no converged reference reachable; labels depend on the Hubbard/magnetic state

Gate semantics (confirmed): 0.02 eV/A applies to **force MAE**. Raw runs: `e3-qe-lux-inputs/qualification-ref/` (not committed); scripts `scripts/e3_qe_ref_sweep.py`, `scripts/sbatch_e3_qe_ref.sh`, `scripts/e3_qe_force_compare.py`. Same pw.in as the pilot label except the keys listed. 1 node GPU build each; ~29 node-hours total.

### Result in one line
No setting reached conv_thr below ~1e-4 Ry (LiFePO4) or ~5e-4 Ry (FCC). A genuinely converged tight reference was **not** obtainable. What the sweep shows instead is that the scatter between labels comes from **which metastable DFT+U / magnetic SCF state is landed in**, not from conv_thr.

### 28-atom LiFePO4 f0019 (best-effort SCF floor, conv_thr 1e-7, up to 250 it, diago_full_acc=.true. in all)

| variant (changed vs pilot) | best est. acc (Ry) | tot / abs mag | outcome |
|---|---|---|---|
| fixed occupations, tot_magnetization=16, beta 0.3 | 2.4e-4 (54 it before stop) | 16.00 / 16.04 | stall |
| gaussian 3.7 mRy, beta 0.1, ndim 20 | 2.7e-4 | 16.00 / 16.05 | stall |
| mv 5 mRy, beta 0.2, ndim 20 | 2.3e-4 | 16.00 / 16.05 | stall |
| m-p 10 mRy, beta 0.1, ndim 20 | 3.5e-4 | 16.00 / 16.05 | stall |
| fixed occ, local-TF, beta 0.1, ndim 20 | **8.9e-5** (250 it) | 16.00 / 16.04 | stall, best of all |
| fixed occ, TF, beta 0.05, ndim 25 | 2.1e-4 | 16.00 / 16.04 | stall |
| fixed occ, beta 0.2, ndim 16, Fe starting_magnetization 0.5 | 2.0e-4 | 16.00 / 16.04 | stall (extra spin start: same moments) |
| fixed occ, HUBBARD {ortho-atomic}, beta 0.3 | 1.2e-4 | 16.00 / 16.04 | stall (not a projector-nonorthogonality issue) |
| fixed occ, diagonalization='cg' | 2.5e-1 after 11 it | 16.00 / 16.06 | far too slow, cancelled |

Observations: (a) the 1e-4 floor is independent of smearing (fixed occupations in a 3.7 eV-gap system removes smearing entirely), mixing mode/beta/ndim and projector choice; (b) the same system without +U converges to 9e-9 Ry in 39 it (`diag-noU`), so the floor is a property of the +U SCF problem (CPU pw.x 7.13 shows it too); (c) total/absolute moment is 16.00/16.04-16.05 in every variant, so the spin state is stable and the stall is in the Hubbard occupations/orbital order, not in the spin state; (d) starting_magnetization variants gave no different moment.

### Labels at the plateau: multiple metastable Hubbard states

Total energies (Ry) of runs that ended at different SCF states for the same f0019 geometry and k-mesh:

| run | E (Ry) | note |
|---|---|---|
| pilot (conv 2e-3, gaussian) | -2098.92156 | |
| conv 5e-4 (round 1, gaussian) | -2098.92186 | same basin as pilot |
| fixed occ, beta 0.3, plain mixing, plateau (90 it) | -2098.92119 | same basin |
| gaussian, beta 0.3, plateau (90 it, end acc 5e-4) | -2098.92923 | 7 mRy lower |
| fixed occ, local-TF, plateau (90 it) | -2098.90377 | **18 mRy higher** |
| fixed occ, local-TF, conv 3e-4 (converged, 23 it) | -2098.90424 | **18 mRy higher**, reached its own conv_thr |

For f0024 the local-TF conv 3e-4 run (88 it, converged) is at -2098.95592 vs pilot -2098.94557 (**10 mRy lower**).
So different mixers land in states 0.1-0.25 eV/cell (4-9 meV/atom) apart, each stable to the SCF criterion. The Hubbard occupation matrix has several near-degenerate minima (Fe2+ minority-spin orbital order) and the pilot state is not the lowest for f0024.

Force MAE / rms / max between states (eV/A; gate on MAE = 0.02):

| pair | dE (meV/atom) | MAE | rms | max |
|---|---|---|---|---|
| f0019 pilot vs conv 5e-4 (same basin, round 1) | 0.15 | **0.006** | 0.013 | 0.077 |
| f0019 pilot vs fixed/plain plateau | 0.18 | 0.087 | 0.122 | 0.410 |
| f0019 pilot vs gaussian plateau | -3.7 | 0.058 | 0.084 | 0.279 |
| f0019 pilot vs fixed/local-TF conv 3e-4 | 8.4 | 0.084 | 0.117 | 0.358 |
| f0019 fixed/plain plateau vs local-TF plateau | 8.5 | 0.062 | 0.096 | 0.340 |
| f0024 pilot vs local-TF conv 3e-4 | -5.0 | **0.118** | 0.166 | 0.495 |
| f0024 pilot vs fixed/plain plateau | 1.7 | 0.077 | 0.105 | 0.348 |

Caveat: "plateau" rows use the forces QE prints from the last iterate of a non-converged SCF (`scf_must_converge=.false.`, 90 it, end accuracy 3e-4..2.6e-3 Ry); they bound the scatter but are not labels. The converged-at-3e-4 rows are legitimate labels in their own state. Same state / only conv_thr changes (0.006 MAE) is fine; **different state changes forces by 0.06-0.12 MAE**, 3-6x over the gate. dE is always <9 meV/atom, 10x under the 100 meV/atom energy gate.

### Cutoff vs SCF (x1.2 SSSP cutoff: ecutwfc 108 / ecutrho 1296 Ry)
f0019, pilot-like settings (gaussian, beta 0.3), conv 5e-4, converged in 40 it (0.17 h): vs the same settings at SSSP cutoff: **MAE 0.038, rms 0.067, max 0.281 eV/A**, offset dE = +39.9 meV/atom (a near-constant shift; consistent across frames it does not affect relative energies much). Vs pilot: MAE 0.038. So the cutoff effect alone (0.04 MAE) is about the same size as the state effect and above the gate. Not run for FCC (cost).

### 128-atom FCC Cantor f0021 (mv 10 mRy kept, spin; conv_thr 1e-6 unless noted, diago_full_acc, ndim 20, 300 it)

| variant | best est. acc (Ry) | tot / abs mag at end | outcome |
|---|---|---|---|
| mv 0.01, beta 0.05 | 4.9e-4 (300 it) | 56.3 / 120.0 | no conv, floor ~5e-4 |
| mv 0.01, beta 0.1, TF | 4.7e-3 | 5.7 / 71 (collapsed to a different magnetic state) | cancelled |
| mv 0.02, beta 0.1 | 5.6e-4 | 54.3 / 118.0 | no conv |
| gaussian 0.02, beta 0.1 | 4.7e-4 | 53.0 / 113.3 | no conv |
| mv 0.01, beta 0.05, conv_thr 6e-4 | stalls 8e-4 (196 it) | 56.9 / 117 | cancelled |
| mv 0.01, beta 0.05, **conv 1e-3** | 9.7e-4 (64 it) | **56.60 / 114.3** | converged (label R1) |
| mv 0.01, beta 0.1, **conv 1e-3** | 9.4e-4 (70 it) | **56.68 / 114.4** | converged (label R2) |

Three independent conv-1e-3 runs now exist (round-1 run, R1, R2). Force MAE between them: R1-R2 0.021, round1-R2 0.023, round1-R1 0.031 (rms 0.035-0.046, max 0.15-0.20). Versus the pilot (conv ~4e-3, stopped at 4e-3): R1 0.069, R2 0.065 (rms ~0.11, max 0.42-0.45); dE ~1.2 meV/atom. Total magnetization drifts with tightening: pilot 54.6, round-1 1e-3 run 55.2, R1/R2 56.6-56.7, abs 110 -> 114. So the pilot label is not magnetically converged either, and even conv 1e-3 labels scatter at ~0.02-0.03 MAE (at the gate). FCC floor is ~5e-4 Ry; below that no run converged.

### Recommendations (magnetic materials)
1. Do **not** claim force-MAE qualification at 0.02 eV/A for LiFePO4 or FCC Cantor with these settings. State this honestly in any label card: force noise is MAE ~0.06-0.12 (LiFePO4, set by metastable Hubbard-state selection) and ~0.07 (FCC pilot, 4e-3) / ~0.02-0.03 (FCC conv 1e-3).
2. FCC Cantor: use `conv_thr = 1e-3`, `mixing_beta 0.05-0.1`, `mixing_ndim 20`, `diago_full_acc=.true.`, `electron_maxstep 300`, mv 0.01 unchanged. It converges in 64-70 it (~1 h/node, cheaper than the pilot-style runs that needed 80-300 it) and cuts force error from ~0.07 to ~0.02-0.03 MAE. Cost is small; tighter than 1e-3 is not reachable (floor ~5e-4).
3. LiFePO4 +U: conv_thr 3e-4 to 5e-4 is the reachable ceiling (3e-4 converged in 23 it for f0019, 88 it for f0024, 0.2-0.5 h on 1 node with `occupations='fixed'`, `tot_magnetization=16`, `mixing_mode='local-TF'`, beta 0.1, ndim 20, `diago_full_acc`). But conv_thr alone does not fix the label: the converged state depends on the mixer. Fixed occupations (valid for this gapped system, moment 16 muB integer) is cleaner than gaussian smearing and removes one source of drift. If LiFePO4 stays in the campaign, either (a) use one fixed protocol for every frame and accept MAE ~0.06-0.12 vs the "other" basin, documenting the force-error budget, or (b) exclude/downweight LiFePO4 forces (train on energies plus forces with a larger per-structure sigma). A real fix needs a state-selection step (e.g. a few starting Hubbard occupations/`starting_ns_eigenvalue` or quench-and-pick-lowest per frame), not run here.
4. Cutoff: x1.2 cutoff changes LiFePO4 f0019 forces by 0.038 MAE, so the production cutoff itself contributes to the force error; a cutoff-converged reference for the gate would need the larger cutoff.
5. Not tried: `starting_ns_eigenvalue`/occupation-matrix control, `lda_plus_u_kind=1`, tighter-than-atomic projectors (ortho-atomic gave the same floor), restart-from-converged-density ladders, FCC at x1.2 cutoff, 112-atom LiFePO4.
