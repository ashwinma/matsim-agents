# E3-QE reference inputs on Lux (validation sets + elemental references)

Generated with `scripts/e3_qe_reference_inputs.py` (+ `scripts/sbatch_e3_qe_reference.sh`),
outputs under `/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval/e3-qe-lux-inputs/`:

- `validation-<material>.extxyz` (+ `.manifest.json`): 32 QE-labelled held-out frames per material
  (seeded rattle 0.04 A + 3 volume variants of the repo's seed/POSCAR structures; recipe in the script).
- `elemental/manifests/<material>/elemental-references.json`: per-MATERIAL, not one global file, because
  cutoffs/smearing (and so the QE method signature) differ per material.
- `env/check-material.sh <material>`: CPU-only `qe_active_learning check` with these inputs wired in
  (uses `MATSIM_E3_OBJECTIVES_PATH` = Lux objectives file, `MATSIM_E3_MLIP_STRUCTURES_PER_ROUND=64`).
- `diag-*`, `diagfcc*`, `superseded/`: diagnostics and failed/slow attempts, kept as evidence.

## Assumptions for Max's review

| Item | What we did | Why / evidence |
|---|---|---|
| Fe reference | Plain PBE, no U (U=5.3 eV only inside LiFePO4) | Materials Project mixed GGA/GGA+U convention. Fe bcc +U never relaxed (3 attempts). Does the formation-energy comparison apply an MP-style mixing correction? |
| Elemental phases | One or two candidate phases per element, lowest energy kept: Nb/Ta/V/Li bcc; Hf/Zr/Ti/Zn hcp; Ni fcc; Co hcp+fcc; Fe/Cr/Mn bcc (+Mn fcc); C graphite+diamond; P black; O2 triplet and H2 in boxes | ASE ideal-lattice starting geometries (experimental lattice constants, hard-coded in the script), relaxed with the per-material QE settings |
| Magnetic states | Ni/Co/Fe/Cr/Mn: ferromagnetic start (Max's muB values converted to starting_magnetization); no AFM tried | Cr and Mn are antiferromagnetic in reality; FM start is the specified protocol but may give higher-energy references |
| Validation cells | LiFePO4: 6 frames of the 28-atom olivine cell + 26 of 112-atom supercells; FCC Cantor 128 atoms; BCC 128 atoms; Nb-Ta-O 28; Zn-formate COD 7205949 (216); phosphorene 2-16 | From repo seed/POSCAR sets; Zn-formate uses COD only (alpha/beta seeds have no H) |
| k-meshes | The env-lux values (one per material, applied to every cell) | Same as step 2 of the plan |

## SCF settings that differ from the env-lux defaults (needed to converge on Lux)

The Lux `pw.x` GPU build shows an SCF accuracy floor with large magnetic/DFT+U cells; conv_thr=1e-8 is unreachable there.
Evidence: 28-atom LiFePO4+U plateaus at ~2e-4 Ry for beta 0.1/0.2/0.3, local-TF, ndim 12, ortho-atomic and
`diago_full_acc`, while the same cell without U converges to 1e-8 in 39 iterations.
All the frames below are marked converged only if pw.x prints "convergence has been achieved" and JOB DONE.

| Material | Frames | Override of `extra_electrons` | Note |
|---|---|---|---|
| phosphorene, nb_ta_o, zn_formate_mof | all | none | mixing_beta 0.3, conv_thr 1e-8 |
| bcc_refractory | 0,3,8 | none | the other 29 frames use mixing_beta 0.1, mixing_ndim 12 (beta 0.3 diverged or stalled on 6 of 9 frames) |
| lifepo4 (PBE+U) | all | conv_thr 2e-3 | 112-atom floor is ~1e-3..2e-3 Ry. 28-atom check: conv_thr 1e-3 vs 5e-4 gives rms dF 0.028, max 0.14 eV/A, dE 0.4 meV/atom |
| fcc_cantor | all | mixing_beta 0.1, mixing_ndim 12, electron_maxstep 300, conv_thr 5e-3 | beta 0.3 diverged (1e4 Ry); beta 0.1 reaches a 3e-4..1e-2 Ry floor |

**Consequence for the AL run:** the same overrides must be applied to LiFePO4 and FCC Cantor in `e3_qe_mace_lux.yaml`
(`extra_electrons`), otherwise their DFT labels will never converge. Max's call: accept a looser conv_thr, or look at
the pw.x GPU build.

## Timeouts

LiFePO4 112-atom frames need ~1 h SCF + ~1 h forces/stress; frames were run with 9000-15000 s timeouts
(the e3-qe yaml's `timeout_sec: 1800` is far too small for them and for the 128-atom cells). Two Lux nodes ran
~10x slower than the rest (Zn-formate f0024, LiFePO4 f0001); those frames were rerun on other nodes.
