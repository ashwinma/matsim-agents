# Reviewed shell input for E3-QE/MACE, material=lifepo4, Lux.
# source this, then: python -m benchmarks.e3.qe_active_learning run \
#   --material lifepo4 --config examples/active_learning/e3_qe_mace_lux_lifepo4.yaml --approve-compute
#
# NOTE: LiFePO4 uses the DEDICATED e3_qe_mace_lux_lifepo4.yaml (pw_template
# path, PBE+U on Fe 3d), NOT the generic e3_qe_mace_lux.yaml -- do not pass
# the generic config for this material. ecutwfc/ecutrho/occupations/
# smearing/degauss/SYSTEM/kpts are already baked into
# examples/active_learning/pw_lifepo4.template and that yaml, so this file
# only exports the run/pseudopotential/validation plumbing.

export PW_BIN="${PW_BIN:?set GPU-enabled pw.x, e.g. pw.x from the qe/develop_omp5_76omp-lux-tuned module}"
export PSEUDO_DIR="${SSSP_PSEUDO_DIR:?TODO: point at the fetched SSSP 1.3.0 PBE-efficiency UPF dir -- not located on disk in this pass, see README.md}"
export E3_QE_RUN_DIR="${E3_QE_LUX_ROOT:?set a Lux QE-study root dir}/e3-qe-lux/lifepo4"
export E3_QE_VALIDATION_SET="${E3_QE_VALIDATION_SET:?provide independent QE-labelled held-out extxyz for lifepo4 -- not yet prepared}"
export ELEMENTAL_REFERENCE_MANIFEST="${ELEMENTAL_REFERENCE_MANIFEST:?provide DFT-labelled elemental JSON manifest -- not yet prepared}"

# TODO: confirm exact UPF filenames once $SSSP_PSEUDO_DIR is populated.
export E3_QE_PSEUDOPOTENTIALS='{Fe: Fe.UPF, Li: Li.UPF, O: O.UPF, P: P.UPF}'

export E3_FORCE_ERROR_TOLERANCE=0.2
export E3_QE_PROMOTION_APPROVED=false
