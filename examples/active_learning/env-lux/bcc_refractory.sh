# Reviewed shell input for E3-QE/MACE, material=bcc_refractory, Lux.
# source this, then: python -m benchmarks.e3.qe_active_learning run \
#   --material bcc_refractory --config examples/active_learning/e3_qe_mace_lux.yaml --approve-compute
#
# Elements (any 4-6 of): Nb, Ta, V, Hf, Zr, Ti (benchmarks/e3/structure_generation.py
# _ALLOY_ELEMENTS["bcc_refractory"]). PBE, no spin, no U (Max's review).

export PW_BIN="${PW_BIN:?set GPU-enabled pw.x, e.g. pw.x from the qe/develop_omp5_76omp-lux-tuned module}"
export PSEUDO_DIR="${SSSP_PSEUDO_DIR:?TODO: point at the fetched SSSP 1.3.0 PBE-efficiency UPF dir -- not located on disk in this pass, see README.md}"
export E3_QE_RUN_DIR="${E3_QE_LUX_ROOT:?set a Lux QE-study root dir}/e3-qe-lux/bcc_refractory"
export E3_QE_VALIDATION_SET="${E3_QE_VALIDATION_SET:?provide independent QE-labelled held-out extxyz for bcc_refractory -- not yet prepared}"
export ELEMENTAL_REFERENCE_MANIFEST="${ELEMENTAL_REFERENCE_MANIFEST:?provide DFT-labelled elemental JSON manifest -- not yet prepared}"

# TODO: confirm exact UPF filenames once $SSSP_PSEUDO_DIR is populated.
export E3_QE_PSEUDOPOTENTIALS='{Nb: Nb.UPF, Ta: Ta.UPF, V: V.UPF, Hf: Hf.UPF, Zr: Zr.UPF, Ti: Ti.UPF}'

# ecutwfc = max over the FULL allowed element set (any subset may appear in a
# given structure): Nb=40, Ta=45, V=40, Hf=50, Zr=30, Ti=40 Ry
# (src/matsim_agents/backends/dft/qe_relax.py _ECUTWFC_RY) -> max=50 (Hf).
# ecutrho = ecutwfc * 8, same convention as recommend_settings().
export E3_QE_ECUTWFC_RY=50
export E3_QE_ECUTRHO_RY=400

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

export E3_FORCE_ERROR_TOLERANCE=0.2
export E3_QE_PROMOTION_APPROVED=false
