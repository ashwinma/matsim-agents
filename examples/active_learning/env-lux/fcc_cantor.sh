# Reviewed shell input for E3-QE/MACE, material=fcc_cantor, Lux.
# source this, then: python -m benchmarks.e3.qe_active_learning run \
#   --material fcc_cantor --config examples/active_learning/e3_qe_mace_lux.yaml --approve-compute
#
# Elements (any 4-5 of): Cr, Mn, Fe, Co, Ni (benchmarks/e3/structure_generation.py
# _ALLOY_ELEMENTS["fcc_cantor"]). PBE, collinear spin-polarized, ferromagnetic
# start (Max's review).

export PW_BIN="${PW_BIN:?set GPU-enabled pw.x, e.g. pw.x from the qe/develop_omp5_76omp-lux-tuned module}"
export PSEUDO_DIR="${SSSP_PSEUDO_DIR:-/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/perf-tools/qe-lux/pseudo/sssp-1.3-pbe-efficiency/selected}"
export E3_QE_RUN_DIR="${E3_QE_LUX_ROOT:?set a Lux QE-study root dir}/e3-qe-lux/fcc_cantor"
export E3_QE_VALIDATION_SET="${E3_QE_VALIDATION_SET:?provide independent QE-labelled held-out extxyz for fcc_cantor -- not yet prepared}"
export ELEMENTAL_REFERENCE_MANIFEST="${ELEMENTAL_REFERENCE_MANIFEST:?provide DFT-labelled elemental JSON manifest -- not yet prepared}"

# Real SSSP 1.3.0 PBE-efficiency UPF filenames, from $PSEUDO_DIR/README.md.
# SHA-256 of each: see examples/active_learning/env-lux/SSSP-sha256.txt.
export E3_QE_PSEUDOPOTENTIALS='{Cr: cr_pbe_v1.5.uspp.F.UPF, Mn: mn_pbe_v1.5.uspp.F.UPF, Fe: Fe.pbe-spn-kjpaw_psl.0.2.1.UPF, Co: Co_pbe_v1.2.uspp.F.UPF, Ni: ni_pbe_v1.4.uspp.F.UPF}'

# ecutwfc/ecutrho = max over the full 5-element set, taken independently per
# the real SSSP 1.3.0 PBE-efficiency table in $PSEUDO_DIR/README.md (NOT the
# codebase's rounded qe_relax.py _ECUTWFC_RY table): Cr 40.0/320.0,
# Mn 65.0/780.0, Fe 90.0/1080.0, Co 45.0/360.0, Ni 45.0/360.0 ->
# max_wfc=90.0 (Fe), max_rho=1080.0 (Fe).
export E3_QE_ECUTWFC_RY=90.0
export E3_QE_ECUTRHO_RY=1080.0

# NOT given explicitly by Max (he gave bcc_refractory's mesh only). ASSUMED
# by direct crystallographic analogy to bcc_refractory's explicit 2x2x2:
# same tier range {4,8,16,32,64}, similar primitive-cell scale (fcc a=3.6 A
# vs bcc a=3.0 A, benchmarks/e3/structure_generation.py), same "metallic
# alloy" treatment. FLAG FOR MAX: this is NOT independently computed from a
# real supercell geometry (the generator's actual repeat factorization
# depends on which 4-5 elements/tier the LLM picks that round, so no single
# fixed cell exists to compute from) -- please confirm or correct.
export E3_QE_KPTS='[2, 2, 2]'

export E3_QE_OCCUPATIONS=smearing
export E3_QE_SMEARING=mv
export E3_QE_DEGAUSS_RY=0.01

# Collinear spin-polarized, ferromagnetic start: ~3 muB on Cr/Mn/Fe/Co,
# 0.6 muB on Ni (Max, verbatim). QE's starting_magnetization(i) is a
# FRACTION of species i's pseudopotential valence-electron count (Zval),
# not a raw muB value, and species are indexed in ALPHABETICAL order:
# Co(1), Cr(2), Fe(3), Mn(4), Ni(5). Zval confirmed directly from the real
# UPF headers (`grep -i valence *.UPF` in $PSEUDO_DIR): Co=17, Cr=14, Fe=16,
# Mn=15, Ni=18. ASSUMES the full 5-component alloy is used this round (a
# 4-component sub-alloy would shift these indices and needs its own env
# file/review before that round is dispatched).
#   Co: 3.0 / 17 = 0.1765
#   Cr: 3.0 / 14 = 0.2143
#   Fe: 3.0 / 16 = 0.1875
#   Mn: 3.0 / 15 = 0.2
#   Ni: 0.6 / 18 = 0.0333
export E3_QE_SYSTEM='{nspin: 2, "starting_magnetization(1)": 0.1765, "starting_magnetization(2)": 0.2143, "starting_magnetization(3)": 0.1875, "starting_magnetization(4)": 0.2, "starting_magnetization(5)": 0.0333}'

export E3_FORCE_ERROR_TOLERANCE=0.2
export E3_QE_PROMOTION_APPROVED=false
