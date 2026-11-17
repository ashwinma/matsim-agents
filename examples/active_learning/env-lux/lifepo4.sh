# Reviewed shell input for E3-QE/MACE, material=lifepo4, Lux.
# source this, then: python -m benchmarks.e3.qe_active_learning run \
#   --material lifepo4 --config examples/active_learning/e3_qe_mace_lux.yaml --approve-compute
#
# PBE+U (Fe 3d, U=5.3 eV), collinear spin. Uses the SAME generic
# e3_qe_mace_lux.yaml as every other material: the QE backend emits a native
# HUBBARD card from dft.qe.hubbard_u (qe_relax.write_pw_input), so no
# pw_template is needed -- qe_active_learning.py's validate_config() rejects
# pw_template outright, which conflicted with the earlier template-based plan.
# The old pw_lifepo4.template / e3_qe_mace_lux_lifepo4.yaml are superseded;
# their settings are expressed as structured fields below.

export PW_BIN="${PW_BIN:?set GPU-enabled pw.x, e.g. pw.x from the qe/develop_omp5_76omp-lux-tuned module}"
export PSEUDO_DIR="${SSSP_PSEUDO_DIR:-/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/perf-tools/qe-lux/pseudo/sssp-1.3-pbe-efficiency/selected}"
export E3_QE_RUN_DIR="${E3_QE_LUX_ROOT:?set a Lux QE-study root dir}/e3-qe-lux/lifepo4"
export E3_QE_VALIDATION_SET="${E3_QE_VALIDATION_SET:?provide independent QE-labelled held-out extxyz for lifepo4 -- not yet prepared}"
export ELEMENTAL_REFERENCE_MANIFEST="${ELEMENTAL_REFERENCE_MANIFEST:?provide DFT-labelled elemental JSON manifest -- not yet prepared}"

# Real SSSP 1.3.0 PBE-efficiency UPF filenames, from $PSEUDO_DIR/README.md.
# SHA-256 of each: see examples/active_learning/env-lux/SSSP-sha256.txt.
export E3_QE_PSEUDOPOTENTIALS='{Fe: Fe.pbe-spn-kjpaw_psl.0.2.1.UPF, Li: li_pbe_v1.4.uspp.F.UPF, O: O.pbe-n-kjpaw_psl.0.1.UPF, P: P.pbe-n-rrkjus_psl.1.0.0.UPF}'

# max(Fe 90/1080, Li 40/320, O 50/400, P 30/240 Ry) from the real SSSP table.
export E3_QE_ECUTWFC_RY=90.0
export E3_QE_ECUTRHO_RY=1080.0

# Max, verbatim: 2x4x8 for the 112-atom 2x2x1 olivine supercell.
export E3_QE_KPTS='[2, 4, 8]'

export E3_QE_OCCUPATIONS=smearing
export E3_QE_SMEARING=gaussian
export E3_QE_DEGAUSS_RY=0.0037

# Collinear spin: Fe 5 muB, Li/O/P 0.6 muB (Max). starting_magnetization(i) is
# a FRACTION of species i's Zval; species indexed alphabetically:
# Fe(1), Li(2), O(3), P(4); Zval from the real UPF headers: Fe=16, Li=3, O=6, P=5.
#   Fe 5.0/16=0.3125, Li 0.6/3=0.2, O 0.6/6=0.1, P 0.6/5=0.12
export E3_QE_SYSTEM='{nspin: 2, "starting_magnetization(1)": 0.3125, "starting_magnetization(2)": 0.2, "starting_magnetization(3)": 0.1, "starting_magnetization(4)": 0.12}'

# DFT+U, emitted as: HUBBARD {atomic} / U Fe-3d 5.3
export E3_QE_HUBBARD_U='{Fe-3d: 5.3}'
export E3_QE_HUBBARD_PROJECTOR=atomic

export E3_FORCE_ERROR_TOLERANCE=0.2
export E3_QE_PROMOTION_APPROVED=false

# Per-label SCF settings and timeout (read by e3_qe_mace_lux.yaml).
# Lux GPU pw.x plateaus near 1e-3..2e-3 Ry on 112-atom PBE+U cells; conv_thr 2e-3 is a LOOSE label threshold awaiting Max's approval
# (28-atom check: rms dF 0.03, max 0.14 eV/A).
export E3_QE_EXTRA_ELECTRONS='{conv_thr: 2.0e-3, electron_maxstep: 150, mixing_beta: 0.3}'
export E3_QE_TIMEOUT_SEC=14400  # 112-atom frames took 1.6-2.4 h
