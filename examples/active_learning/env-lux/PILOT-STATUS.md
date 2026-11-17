# E3-QE on Lux: what is approved for the 64-structure pilot (Max, 2026-11-17)

Max approved the 64-structure-per-round pilot on Lux. Its purpose is to verify the whole workflow (candidate
selection, DFT execution, convergence checking, evidence acquisition, model assessment) and to record attempted vs
successful calculations, numerical qualification failures, and cost. It is NOT a production or scientific-accuracy run.

Legend: OK-PILOT = accepted for the pilot only; OPEN = needs work before production; DECIDED = settled.

| Item | Status | What Max said | What it means here |
|---|---|---|---|
| Loose SCF convergence (LiFePO4 `conv_thr` 2e-3; FCC Cantor 5e-3, beta 0.1; BCC beta 0.1) | OK-PILOT | Fine for the pilot, not production-quality labels. 28-atom LiFePO4 rms dF 0.03 eV/A is encouraging but not negligible. | Labels are "pilot labels", not qualified references. Before production: compare against tighter references on a small subset (distorted and magnetically hard frames), judging both energy and force errors; if discrepancies persist, investigate the GPU build or other convergence strategies. |
| Ferromagnetic starts | OK-PILOT | Acceptable if documented as an approximation; not a ground-state claim. | Do not read results as magnetic ground states. Final magnetic moments must be recorded (converged state may differ from the start). AFM/alternative spin states for LiFePO4 and Cantor before physical conclusions. |
| k-meshes: phosphorene 7x5x1, Zn-formate 3x2x2 | OK-PILOT | Reasonable starting points; verify convergence for energies and forces. | Keep Gamma-only along the vacuum direction, check vacuum, and base the Zn-formate mesh on the actual lattice/polymorph. |
| Fixed k-mesh per material (any cell size) | OPEN | Prefer constant reciprocal-space density; scale the mesh with the cell, round, verify. | Current labels for small cells use meshes sized for other cells (LiFePO4 28-atom frames, Nb-Ta-O 28-atom frames, phosphorene 2-16 atoms). Needs a density-based mesh and regenerated labels where they differ. |
| 32 validation frames per material (seeded rattles) | OK-PILOT | Enough for integration and zero-shot screening; not a benchmark. | Frames from the same parent must stay in one partition (no leakage with the AL pool; see `datasets.splits`). Expand to structurally diverse sets later. |
| Lux-hosted LLM | DECIDED | Accepted. | Lux objectives file via `MATSIM_E3_OBJECTIVES_PATH`. |
| PBE vs PBE+U (LiFePO4) | OPEN | Resolve before production. PBE+U (U=5.3 eV, Fe 3d) preferred for new E3-DFT, documented and consistent; keep historical VASP PBE for E2. Never mix PBE and PBE+U labels in one matched accuracy assessment without explicit accounting. | Fe elemental reference is plain PBE; no MP-style correction exists in the workflow. Fixed-composition LiFePO4 comparisons need no Fe reference. |
| Accuracy gates | DECIDED | Do not relax: energy 0.1 eV/atom, force 0.02 eV/A; Max confirmed (2026-11-17) the 0.02 eV/A is the promotion gate on force MAE. Qualify labels independently; flag unqualified labels rather than widening gates. | `promotion_max_force_mae_eV_per_A` in `e3_qe_mace_lux.yaml` is now 0.02. This is strict: a fine-tuned MLIP will rarely meet it, so expect "not promoted" in the pilot; that is a result, not a workflow failure. The separate training trigger (`E3_FORCE_ERROR_TOLERANCE`, 0.2 eV/A) was not addressed by Max and is unchanged. LiFePO4 labels (dF 0.03) are pilot-only. |
| Pilot reporting | DECIDED | Record attempted vs successful calcs, numerical qualification failures, computational costs. | To be added to the pilot run summary. |
| 5000-structure campaign | TABLED | Revisit after the 64-structure campaign. | |
