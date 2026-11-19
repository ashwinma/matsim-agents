#!/bin/bash
# Phosphorene k-mesh convergence scan: relabel a few validation frames with a sequence of k spacings (Gamma-only along vacuum)
# plus Max's fixed 7x5x1. usage: sbatch -N 6 -t 04:00:00 -J kscan-phos scripts/sbatch_kmesh_phos_scan.sh
#SBATCH -A ven136
#SBATCH -p batch
#SBATCH --exclusive
#SBATCH --gpus-per-node=8
#SBATCH -o /lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval/e3-qe-lux-inputs/logs/%x-%j.out
set -uo pipefail
ROOT=/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval
export PROJ_ROOT="${PROJ_ROOT:-$ROOT/wt-qe-kdens}"
export MACE_CHECKPOINT="${MACE_CHECKPOINT:-$HOME/.cache/mace/maceomat0mediummodel}"
export PW_BIN=/lustre/orion/ven136/proj-shared/qe/76omp-bf7acca2/bin/pw.x
export E3_QE_LUX_ROOT=$ROOT/e3-qe-lux-inputs/_unused
mkdir -p /tmp/e3placeholders && : > /tmp/e3placeholders/val.extxyz && echo '{}' > /tmp/e3placeholders/el.json
export E3_QE_VALIDATION_SET=/tmp/e3placeholders/val.extxyz ELEMENTAL_REFERENCE_MANIFEST=/tmp/e3placeholders/el.json
source "$PROJ_ROOT/examples/active_learning/env-lux/phosphorene.sh"
export PYTHONPATH="$PROJ_ROOT/src:$PROJ_ROOT"
OUT=$ROOT/e3-qe-lux-inputs/kmesh-phosphorene
FRAMES="${FRAMES:-1,5,0,2,3,7}"   # 2-atom x2, 4-atom, 16-atom, 12-atom x2
for tag in ${SPACINGS:-s0.272 s0.2 s0.15 s0.1 s0.07 s0.05 s0.035 fixed7x5x1}; do
  unset E3_QE_KPTS E3_QE_KPOINT_SPACING
  case $tag in
    fixed*) export E3_QE_KPTS='[7, 5, 1]' ;;
    s*) export E3_QE_KPOINT_SPACING="[${tag#s}, ${tag#s}, 0]" ;;
  esac
  echo "=== $tag $(date)"
  "$ROOT/e3-qe-lux-inputs/env/venv-host/bin/python" "$PROJ_ROOT/scripts/e3_qe_reference_inputs.py" validation \
    --material phosphorene --nodes "${SLURM_JOB_NUM_NODES:-1}" --only "$FRAMES" --out "$OUT/$tag" --timeout-sec 3600
done
