# Reviewed shell input for E3-QE/MACE, material=zn_formate_mof, Lux.
# source this, then: python -m benchmarks.e3.qe_active_learning run \
#   --material zn_formate_mof --config examples/active_learning/e3_qe_mace_lux.yaml --approve-compute
#
# Elements: C, H, O, Zn (examples/paper_cases/seeds/zn_formate_cod_7205949.cif,
# _chemical_formula_sum "C12 H12 O24 Zn6"). PBE-D3(BJ), no spin, no U
# (Max's review).

export PW_BIN="${PW_BIN:?set GPU-enabled pw.x, e.g. pw.x from the qe/develop_omp5_76omp-lux-tuned module}"
export PSEUDO_DIR="${SSSP_PSEUDO_DIR:?TODO: point at the fetched SSSP 1.3.0 PBE-efficiency UPF dir -- not located on disk in this pass, see README.md}"
export E3_QE_RUN_DIR="${E3_QE_LUX_ROOT:?set a Lux QE-study root dir}/e3-qe-lux/zn_formate_mof"
export E3_QE_VALIDATION_SET="${E3_QE_VALIDATION_SET:?provide independent QE-labelled held-out extxyz for zn_formate_mof -- not yet prepared}"
export ELEMENTAL_REFERENCE_MANIFEST="${ELEMENTAL_REFERENCE_MANIFEST:?provide DFT-labelled elemental JSON manifest -- not yet prepared}"

# TODO: confirm exact UPF filenames once $SSSP_PSEUDO_DIR is populated.
export E3_QE_PSEUDOPOTENTIALS='{C: C.UPF, H: H.UPF, O: O.UPF, Zn: Zn.UPF}'

# ecutwfc = max(C=60, H=60, O=50, Zn=40 Ry, qe_relax.py _ECUTWFC_RY) -> 60.
export E3_QE_ECUTWFC_RY=60
export E3_QE_ECUTRHO_RY=480

# NOT given explicitly by Max ("Gamma-centred k-mesh using the general rule
# above"). Computed from the real COD 7205949 unit cell (orthorhombic,
# a=9.868 A, b=18.2476 A, c=18.14 A, P-type per the CIF's 90/90/90 angles --
# space-group centering not independently re-verified). Insulator -> 20 A
# rule: ceil(20/9.868)=3, ceil(20/18.2476)=2, ceil(20/18.14)=2.
export E3_QE_KPTS='[3, 2, 2]'

export E3_QE_OCCUPATIONS=smearing
export E3_QE_SMEARING=gaussian
export E3_QE_DEGAUSS_RY=0.005

# PBE-D3(BJ) per Max, verbatim.
export E3_QE_SYSTEM='{vdw_corr: dft-d3, dftd3_version: 4}'

export E3_FORCE_ERROR_TOLERANCE=0.2
export E3_QE_PROMOTION_APPROVED=false
