# Reviewed shell input for E3-QE/MACE, material=bcc_refractory, Lux.
# source this, then: python -m benchmarks.e3.qe_active_learning run \
#   --material bcc_refractory --config examples/active_learning/e3_qe_mace_lux.yaml --approve-compute
#
# Elements (any 4-6 of): Nb, Ta, V, Hf, Zr, Ti (benchmarks/e3/structure_generation.py
# _ALLOY_ELEMENTS["bcc_refractory"]). PBE, no spin, no U (Max's review).

export PW_BIN="${PW_BIN:?set GPU-enabled pw.x, e.g. pw.x from the qe/develop_omp5_76omp-lux-tuned module}"
export PSEUDO_DIR="${SSSP_PSEUDO_DIR:-/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/perf-tools/qe-lux/pseudo/sssp-1.3-pbe-efficiency/selected}"
export E3_QE_RUN_DIR="${E3_QE_LUX_ROOT:?set a Lux QE-study root dir}/e3-qe-lux/bcc_refractory"
export E3_QE_VALIDATION_SET="${E3_QE_VALIDATION_SET:?provide independent QE-labelled held-out extxyz for bcc_refractory -- not yet prepared}"
export ELEMENTAL_REFERENCE_MANIFEST="${ELEMENTAL_REFERENCE_MANIFEST:?provide DFT-labelled elemental JSON manifest -- not yet prepared}"

# Real SSSP 1.3.0 PBE-efficiency UPF filenames, from $PSEUDO_DIR/README.md.
# SHA-256 of each: see examples/active_learning/env-lux/SSSP-sha256.txt.
export E3_QE_PSEUDOPOTENTIALS='{Nb: Nb.pbe-spn-kjpaw_psl.0.3.0.UPF, Ta: Ta_pbe_v1.uspp.F.UPF, V: v_pbe_v1.4.uspp.F.UPF, Hf: Hf-sp.oncvpsp.upf, Zr: Zr_pbe_v1.uspp.F.UPF, Ti: ti_pbe_v1.4.uspp.F.UPF}'

# ecutwfc/ecutrho = max over the FULL allowed element set (any subset may
# appear in a given structure), taken independently per the real SSSP 1.3.0
# PBE-efficiency table in $PSEUDO_DIR/README.md (NOT the codebase's rounded
# qe_relax.py _ECUTWFC_RY table, which Max's review asks us to match against
# the actual SSSP recommendation): Nb 40.0/320.0, Ta 45.0/360.0, V 35.0/280.0,
# Zr 30.0/240.0, Hf 50.0/200.0, Ti 35.0/280.0 -> max_wfc=50.0 (Hf),
# max_rho=360.0 (Ta). This exact pair is the README's own worked example.
export E3_QE_ECUTWFC_RY=50.0
export E3_QE_ECUTRHO_RY=360.0

# Max, verbatim: "Gamma-centred 2x2x2 k-mesh for our VASP supercell."
export E3_QE_KPTS='[2, 2, 2]'

# Max: "use smearing for every material" (overrides the auto fixed/smearing
# split in recommend_settings for non-metals too; bcc_refractory is metallic
# either way).
export E3_QE_OCCUPATIONS=smearing
export E3_QE_SMEARING=m-p
export E3_QE_DEGAUSS_RY=0.0147

# PBE, no spin, no U -> no SYSTEM overrides needed.
export E3_QE_SYSTEM='{}'
export E3_QE_HUBBARD_U='{}'

export E3_FORCE_ERROR_TOLERANCE=0.2
export E3_QE_PROMOTION_APPROVED=false

# Per-label SCF settings and timeout (read by e3_qe_mace_lux.yaml).
# 29 of 32 validation frames needed mixing_beta 0.1 / mixing_ndim 12 (beta 0.3 diverged or stalled on 6 of 9 tried).
export E3_QE_EXTRA_ELECTRONS='{conv_thr: 1.0e-8, electron_maxstep: 150, mixing_beta: 0.1, mixing_ndim: 12}'
export E3_QE_TIMEOUT_SEC=7200   # 128-atom frames took up to 25 min

# PILOT-ONLY (Max, 2026-11-17): the loose SCF settings above are accepted for the 64-structure pilot but do NOT yield
# production-quality labels; qualify against tighter references before production. See PILOT-STATUS.md.
