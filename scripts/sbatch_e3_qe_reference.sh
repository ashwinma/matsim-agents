#!/bin/bash
# Run one e3_qe_reference_inputs.py subcommand inside a Lux allocation.
# usage: sbatch -N <n> -t <hh:mm:ss> -J <name> scripts/sbatch_e3_qe_reference.sh <material> <elemental|validation> [extra args...]
#SBATCH -A ven136
#SBATCH -p batch
#SBATCH --exclusive
#SBATCH --gpus-per-node=8
#SBATCH -o /lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval/e3-qe-lux-inputs/logs/%x-%j.out
set -uo pipefail
MATERIAL="$1"; CMD="$2"; shift 2
ROOT=/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval
export PROJ_ROOT="${PROJ_ROOT:-$ROOT/wt-qe-ref}"
export MACE_CHECKPOINT="${MACE_CHECKPOINT:-$HOME/.cache/mace/maceomat0mediummodel}"
export PW_BIN=/lustre/orion/ven136/proj-shared/qe/76omp-bf7acca2/bin/pw.x
export E3_QE_LUX_ROOT="${E3_QE_LUX_ROOT:-$ROOT/e3-qe-lux-inputs/_unused}"
mkdir -p /tmp/e3placeholders && : > /tmp/e3placeholders/val.extxyz && echo '{}' > /tmp/e3placeholders/el.json
export E3_QE_VALIDATION_SET=/tmp/e3placeholders/val.extxyz ELEMENTAL_REFERENCE_MANIFEST=/tmp/e3placeholders/el.json
# shellcheck disable=SC1090
source "$PROJ_ROOT/examples/active_learning/env-lux/$MATERIAL.sh"
export PYTHONPATH="$PROJ_ROOT/src:$PROJ_ROOT"
NODES="${SLURM_JOB_NUM_NODES:-1}"
exec "$ROOT/e3-qe-lux-inputs/env/venv-host/bin/python" "$PROJ_ROOT/scripts/e3_qe_reference_inputs.py" "$CMD" \
  --material "$MATERIAL" --nodes "$NODES" "$@"
