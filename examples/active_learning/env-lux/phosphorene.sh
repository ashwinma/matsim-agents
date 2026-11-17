# Reviewed shell input for E3-QE/MACE, material=phosphorene, Lux.
# source this, then: python -m benchmarks.e3.qe_active_learning run \
#   --material phosphorene --config examples/active_learning/e3_qe_mace_lux.yaml --approve-compute
#
# Elemental P only (black/blue allotropes). PBE, no dispersion, no spin
# (Max's review).

export PW_BIN="${PW_BIN:?set GPU-enabled pw.x, e.g. pw.x from the qe/develop_omp5_76omp-lux-tuned module}"
export PSEUDO_DIR="${SSSP_PSEUDO_DIR:-/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/perf-tools/qe-lux/pseudo/sssp-1.3-pbe-efficiency/selected}"
export E3_QE_RUN_DIR="${E3_QE_LUX_ROOT:?set a Lux QE-study root dir}/e3-qe-lux/phosphorene"
export E3_QE_VALIDATION_SET="${E3_QE_VALIDATION_SET:?provide independent QE-labelled held-out extxyz for phosphorene -- not yet prepared}"
export ELEMENTAL_REFERENCE_MANIFEST="${ELEMENTAL_REFERENCE_MANIFEST:?provide DFT-labelled elemental JSON manifest -- not yet prepared}"

# Real SSSP 1.3.0 PBE-efficiency UPF filename, from $PSEUDO_DIR/README.md.
# SHA-256: see examples/active_learning/env-lux/SSSP-sha256.txt.
export E3_QE_PSEUDOPOTENTIALS='{P: P.pbe-n-rrkjus_psl.1.0.0.UPF}'

# ecutwfc/ecutrho for P = 30.0/240.0 Ry, from the real SSSP 1.3.0
# PBE-efficiency table in $PSEUDO_DIR/README.md.
export E3_QE_ECUTWFC_RY=30.0
export E3_QE_ECUTRHO_RY=240.0

# NOT given explicitly by Max. Computed from the real black-phosphorene seed
# cell (examples/paper_cases/seeds/phosphorene_black_P.extxyz, 4 atoms,
# in-plane a=3.3 A, b=4.62 A, vacuum c=20.24 A -- the minimum generated tier,
# dense k-mesh is conservative/safe for larger tiers too). Insulator -> 20 A
# rule: ceil(20/3.3)=7, ceil(20/4.62)=5, vacuum axis -> 1 (matches
# recommend_settings()'s own 2D/slab flattening).
# CAVEAT: blue phosphorene's seed cell differs (2 atoms, ~3.28 x 3.28 A,
# examples/paper_cases/seeds/phosphorene_blue_P.extxyz) and would want its
# own mesh (~[7, 4, 1] at its minimum tier) -- this file picks black
# phosphorene (the catalog's dominant/first action) as the single
# representative value. FLAG FOR MAX if blue phosphorene is exercised
# heavily enough that this matters.
export E3_QE_KPTS='[7, 5, 1]'

export E3_QE_OCCUPATIONS=smearing
export E3_QE_SMEARING=gaussian
export E3_QE_DEGAUSS_RY=0.005

# PBE, no dispersion, no spin -> no SYSTEM overrides needed. 20.24 A of
# vacuum in both seed cells already clears Max's "at least 15 A, converged
# by 20 A" bar -- no change needed there.
export E3_QE_SYSTEM='{}'
export E3_QE_HUBBARD_U='{}'

export E3_FORCE_ERROR_TOLERANCE=0.2
export E3_QE_PROMOTION_APPROVED=false

# Per-label SCF settings and timeout (read by e3_qe_mace_lux.yaml).
export E3_QE_EXTRA_ELECTRONS='{conv_thr: 1.0e-8, electron_maxstep: 150, mixing_beta: 0.3}'
