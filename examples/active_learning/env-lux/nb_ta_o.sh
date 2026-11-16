# Reviewed shell input for E3-QE/MACE, material=nb_ta_o, Lux.
# source this, then: python -m benchmarks.e3.qe_active_learning run \
#   --material nb_ta_o --config examples/active_learning/e3_qe_mace_lux.yaml --approve-compute
#
# Elements: Nb, Ta, O (benchmarks/e3/structure_generation.py _OXIDE_FORMULAS:
# Nb2O5, Ta2O5, NbTaO5, NbO2, TaO2, NbTaO4). PBE, no U, no spin (Max's
# review). Reference phases for formation-energy comparisons: Nb and Ta
# metals; NbO, NbO2, Nb2O5, TaO2, Ta2O5; and the pilot-pool ternaries.

export PW_BIN="${PW_BIN:?set GPU-enabled pw.x, e.g. pw.x from the qe/develop_omp5_76omp-lux-tuned module}"
export PSEUDO_DIR="${SSSP_PSEUDO_DIR:-/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/perf-tools/qe-lux/pseudo/sssp-1.3-pbe-efficiency/selected}"
export E3_QE_RUN_DIR="${E3_QE_LUX_ROOT:?set a Lux QE-study root dir}/e3-qe-lux/nb_ta_o"
export E3_QE_VALIDATION_SET="${E3_QE_VALIDATION_SET:?provide independent QE-labelled held-out extxyz for nb_ta_o -- not yet prepared}"
export ELEMENTAL_REFERENCE_MANIFEST="${ELEMENTAL_REFERENCE_MANIFEST:?provide DFT-labelled elemental JSON manifest -- not yet prepared}"

# Real SSSP 1.3.0 PBE-efficiency UPF filenames, from $PSEUDO_DIR/README.md.
# SHA-256 of each: see examples/active_learning/env-lux/SSSP-sha256.txt.
export E3_QE_PSEUDOPOTENTIALS='{Nb: Nb.pbe-spn-kjpaw_psl.0.3.0.UPF, Ta: Ta_pbe_v1.uspp.F.UPF, O: O.pbe-n-kjpaw_psl.0.1.UPF}'

# ecutwfc/ecutrho = max(Nb 40.0/320.0, Ta 45.0/360.0, O 50.0/400.0 Ry), from
# the real SSSP 1.3.0 PBE-efficiency table in $PSEUDO_DIR/README.md -> 50.0/400.0.
export E3_QE_ECUTWFC_RY=50.0
export E3_QE_ECUTRHO_RY=400.0

# benchmarks/e3/protocol.yaml's nb_ta_o.pool is `kind: poscar_dir, path:
# research/nb-ta-o/pilot/poscars` -- i.e. the AL candidate pool for this
# material IS the NbTaO5_ordering_NN.POSCAR set (same supercell, 15 atoms,
# a=12.73 A / b=5.369 A / c=4.88 A, differing only in Nb/Ta/O ordering).
# Every ordering already has a real, policy-documented KPOINTS file under
# research/nb-ta-o/pilot/vasp_inputs/{production-candidates,
# ordering-family-pending-approval}/NbTaO5_ordering_NN/KPOINTS.json:
# {"policy": "gamma_centered_target_spacing", "target_spacing_A^-1": 0.15,
# "mesh_dimensions": [4, 8, 9]}. Checked across orderings 01/05/06/09/12 --
# identical mesh and cell in every case, so this is a real, already-computed
# value, not a placeholder. (The separate elemental/binary/ternary reference
# phases Max also lists -- Nb/Ta metals, NbO/NbO2/Nb2O5/TaO2/Ta2O5 -- are a
# genuinely separate, not-yet-approved inventory in
# research/nb-ta-o/pilot/{elemental,binary,ternary}_reference_inventory.json;
# those are for formation-energy reference calculations, not this AL loop's
# candidate-pool QE audits, and still need Max's/a reviewer's sign-off
# before any VASP/QE work is run against them.)
export E3_QE_KPTS='[4, 8, 9]'

export E3_QE_OCCUPATIONS=smearing
export E3_QE_SMEARING=mv
# Max gave a range (0.005-0.01 Ry); using the documented midpoint.
export E3_QE_DEGAUSS_RY=0.0075

# PBE, no U, no spin -> no SYSTEM overrides needed.
export E3_QE_SYSTEM='{}'

export E3_FORCE_ERROR_TOLERANCE=0.2
export E3_QE_PROMOTION_APPROVED=false
