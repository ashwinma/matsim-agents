# QE convergence tests (cutoff +20% and phosphorene vacuum)

Setup: one validation frame per material, original `pw.in` (same SCF overrides, k-mesh, Hubbard U), with only
`ecutwfc`/`ecutrho` scaled x1.2 (cutoff test) or the c axis changed (vacuum test). Baseline = the original validation
`pw.out` of the same frame. Outputs: `e3-qe-lux-inputs/convergence/<task>/{pw.in,pw.out,result.json}`, summary in
`convergence/summary.json`. Driver: `scripts/e3_qe_convergence.py` (`report` regenerates the table).
All 12 tasks finished (`JOB DONE`, SCF converged). The `srun ... Aborted (core dumped)` lines at the end of each
`pw.out` are post-completion teardown noise, not failures. Re-running two tasks at 1.0x (fcc_cantor-control,
lifepo4-28-control) reproduces the baseline bit-for-bit (dE = 0, dF = 0), so the differences below are purely the cutoff.

## Cutoff test (SSSP cutoffs vs x1.2)

| material | frame | atoms | ecutwfc/ecutrho (Ry) -> x1.2 | dE (meV/atom) | max dF (eV/A) | rms dF (eV/A) | max dStress (kbar) |
|---|---|---|---|---|---|---|---|
| phosphorene | f0000 | 4 | 30/240 -> 36/288 | -0.82 | 0.0014 | 0.0008 | 0.09 |
| bcc_refractory | f0026 | 128 | 50/360 -> 60/432 | -1.51 | 0.0005 | 0.0001 | 1.32 |
| nb_ta_o | f0008 | 28 | 50/400 -> 60/480 | -5.66 | 0.0080 | 0.0026 | 2.53 |
| zn_formate_mof | f0015 | 216 | 60/480 -> 72/576 | -6.28 | 0.0123 | 0.0039 | 0.10 |
| fcc_cantor | f0000 | 128 | 90/1080 -> 108/1296 | -2.76 | 0.0822 | 0.0183 | 1.36 |
| lifepo4 (28 atoms) | f0029 | 28 | 90/1080 -> 108/1296 | -3.39 | 0.1257 | 0.0339 | 4.60 |
| lifepo4 (112 atoms) | f0013 | 112 | 90/1080 -> 108/1296 | -1.12 | 0.1192 | 0.0234 | 1.57 |

Wall time at x1.2: phosphorene 31 s, zn_formate 0.15 h, nb_ta_o 0.23 h, bcc 0.35 h, lifepo4-28 0.14 h, fcc 1.23 h,
lifepo4-112 2.37 h (1 Lux node each, 8 GPUs).

## Phosphorene vacuum test (baseline c = 20.24 A)

| c (A) | dE (meV/atom) | max dF (eV/A) |
|---|---|---|
| 15 | -0.003 | 0.0003 |
| 25 | +0.001 | 0.0001 |
| 30 | -0.001 | 0.00007 |

Vacuum is converged: even c = 15 A is within 0.003 meV/atom and 0.0004 eV/A of c = 20.24 A; c = 25/30 A change nothing.
(Reported stress components scale with 1/c because QE normalizes to cell volume; use forces/energy, not the raw stress, for this check.)

## Verdict (criteria: 1 meV/atom, ~0.01 eV/A)

| material | energy (<1 meV/atom absolute) | forces (<~0.01 eV/A) | verdict |
|---|---|---|---|
| phosphorene | yes (0.82) | yes | converged |
| bcc_refractory | marginal (1.5) | yes (0.0005) | forces converged; absolute E marginal |
| nb_ta_o | no (5.7) | yes (0.008) | forces converged; absolute E not |
| zn_formate_mof | no (6.3) | marginal (0.012) | forces ~converged; absolute E not |
| fcc_cantor | no (2.8) | no (0.082 max, 0.018 rms) | not converged to strict criteria |
| lifepo4 | no (1.1-3.4) | no (0.12 max, 0.02-0.03 rms) | not converged to strict criteria |

Interpretation:
- Absolute total energies shift by 1-6 meV/atom for every material except phosphorene. This is the usual Pulay/basis-set
  offset and is mostly a near-constant shift across configurations of the same composition. It matters for
  absolute energies and cross-composition comparison, much less for energy differences and forces. With a single frame
  per material this test cannot show whether the *relative* energy error is below 1 meV/atom; that needs a second frame
  at both cutoffs (not run).
- Force errors are fine (<= ~0.01 eV/A) for phosphorene, bcc_refractory, nb_ta_o, zn_formate_mof.
- fcc_cantor and lifepo4 (the 90/1080 Ry SSSP-precision cutoffs, Fe/Ni/Co/Cr/Mn and Fe/Mn U-systems) show max force
  differences of 0.08-0.13 eV/A (rms 0.02-0.03), i.e. above the 0.01 eV/A target, so these labels carry a basis-set force
  noise comparable to the 0.02 eV/A force gate. Note the 128-atom lifepo4/fcc rms is lower than the 28-atom one, but max dF
  is a few single-atom outliers (heavy-core atoms).
- Recommendation: keep SSSP cutoffs for phosphorene, bcc_refractory, nb_ta_o, zn_formate_mof. For fcc_cantor and lifepo4,
  either accept ~0.1 eV/A worst-case label noise (document it), or raise cutoffs ~20% (cost: 1.1-1.3x wall at 128 atoms
  was ~1.07 h baseline vs 1.23 h, i.e. only ~15% more) -- the +20% cost is small, so raising is cheap if Max wants strict
  convergence; a x1.2 re-test would then still need a x1.4 check to confirm a plateau (not run).
- Vacuum: 20.24 A is ample for phosphorene (15 A would suffice).
