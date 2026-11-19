# Constant reciprocal-space k-sampling density (Max, 2026-11-17), per material.
# usage: source env-lux/<material>.sh; source env-lux/kdensity.sh <material>
# Per-axis spacing in 1/A (2*pi included) derived from Max's reference mesh on its reference cell
# (scripts/e3_qe_kmesh_spacings.py); 0 = Gamma-only axis (vacuum). Each structure gets
# n_i = max(1, round(2*pi*|b_i|/spacing_i)). Replaces the fixed E3_QE_KPTS mesh.
unset E3_QE_KPTS
case "${1:?material}" in
  lifepo4) export E3_QE_KPOINT_SPACING='[0.151, 0.1301, 0.1661]' ;;  # reference: 2x4x8 on the 112-atom 2x2x1 supercell
  bcc_refractory) export E3_QE_KPOINT_SPACING='[0.235, 0.235, 0.235]' ;;  # reference: 2x2x2 on the 128-atom cell
  fcc_cantor) export E3_QE_KPOINT_SPACING='[0.2196, 0.2196, 0.4393]' ;;  # reference: 2x2x2 on the 128-atom cell (14.304x14.304x7.152 A)
  nb_ta_o) export E3_QE_KPOINT_SPACING='[0.1278, 0.1463, 0.1431]' ;;  # reference: 4x8x9 on the 15-atom pilot cell (KPOINTS.json, 0.15 1/A)
  phosphorene) export E3_QE_KPOINT_SPACING='[0.07, 0.07, 0]' ;;  # converged scan (env-lux/KMESH-PHOSPHORENE.md); Max's 7x5x1 (=0.272) is NOT converged; Gamma-only along vacuum
  zn_formate_mof) export E3_QE_KPOINT_SPACING='[0.2122, 0.1722, 0.1732]' ;;  # reference: 3x2x2 on the COD 7205949 cell
  *) echo "unknown material $1" >&2; return 1 ;;
esac
