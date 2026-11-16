# Reviewed shell input for E3-QE/MACE, material=nb_ta_o, Lux.
# source this, then: python -m benchmarks.e3.qe_active_learning run \
#   --material nb_ta_o --config examples/active_learning/e3_qe_mace_lux.yaml --approve-compute
#
# Elements: Nb, Ta, O (benchmarks/e3/structure_generation.py _OXIDE_FORMULAS:
# Nb2O5, Ta2O5, NbTaO5, NbO2, TaO2, NbTaO4). PBE, no U, no spin (Max's
# review). Reference phases for formation-energy comparisons: Nb and Ta
# metals; NbO, NbO2, Nb2O5, TaO2, Ta2O5; and the pilot-pool ternaries.

export PW_BIN="${PW_BIN:?set GPU-enabled pw.x, e.g. pw.x from the qe/develop_omp5_76omp-lux-tuned module}"
export PSEUDO_DIR="${SSSP_PSEUDO_DIR:?TODO: point at the fetched SSSP 1.3.0 PBE-efficiency UPF dir -- not located on disk in this pass, see README.md}"
export E3_QE_RUN_DIR="${E3_QE_LUX_ROOT:?set a Lux QE-study root dir}/e3-qe-lux/nb_ta_o"
export E3_QE_VALIDATION_SET="${E3_QE_VALIDATION_SET:?provide independent QE-labelled held-out extxyz for nb_ta_o -- not yet prepared}"
export ELEMENTAL_REFERENCE_MANIFEST="${ELEMENTAL_REFERENCE_MANIFEST:?provide DFT-labelled elemental JSON manifest -- not yet prepared}"

# TODO: confirm exact UPF filenames once $SSSP_PSEUDO_DIR is populated.
export E3_QE_PSEUDOPOTENTIALS='{Nb: Nb.UPF, Ta: Ta.UPF, O: O.UPF}'

# ecutwfc = max(Nb=40, Ta=45, O=50 Ry, qe_relax.py _ECUTWFC_RY) -> 50.
export E3_QE_ECUTWFC_RY=50
export E3_QE_ECUTRHO_RY=400

# NOT determinable from this repo: nb_ta_o structures come from AFLOW
# prototypes / pyxtal (benchmarks/e3/structure_generation.py), whose actual
# cell geometry is fetched/generated per-prototype at run time and is not a
# fixed local seed file like the other five materials -- there is no single
# representative cell to apply the 30/20 A rule to ahead of time.
# PLACEHOLDER, matching bcc_refractory/fcc_cantor's floor -- MUST be
# reviewed per the actual prototype cell once a real run selects one; do not
# treat this as converged.
export E3_QE_KPTS='[2, 2, 2]'  # TODO: prototype-dependent, unverified

export E3_QE_OCCUPATIONS=smearing
export E3_QE_SMEARING=mv
# Max gave a range (0.005-0.01 Ry); using the documented midpoint.
export E3_QE_DEGAUSS_RY=0.0075

# PBE, no U, no spin -> no SYSTEM overrides needed.
export E3_QE_SYSTEM='{}'

export E3_FORCE_ERROR_TOLERANCE=0.2
export E3_QE_PROMOTION_APPROVED=false
