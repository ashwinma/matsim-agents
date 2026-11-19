#!/bin/bash
# usage: sbatch -N <n> -t <hh:mm:ss> -J qe-conv scripts/sbatch_e3_qe_convergence.sh [--only a,b]
#SBATCH -A ven136
#SBATCH -p batch
#SBATCH --exclusive
#SBATCH --gpus-per-node=8
#SBATCH -o /lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval/e3-qe-lux-inputs/logs/%x-%j.out
set -uo pipefail
ROOT=/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval
export PROJ_ROOT="${PROJ_ROOT:-$ROOT/wt-qe-conv}"
export MACE_CHECKPOINT="${MACE_CHECKPOINT:-$HOME/.cache/mace/maceomat0mediummodel}"
export PW_BIN=/lustre/orion/ven136/proj-shared/qe/76omp-bf7acca2/bin/pw.x
export E3_QE_LUX_ROOT="$ROOT/e3-qe-lux-inputs/_unused"
mkdir -p /tmp/e3placeholders && : > /tmp/e3placeholders/val.extxyz && echo '{}' > /tmp/e3placeholders/el.json
export E3_QE_VALIDATION_SET=/tmp/e3placeholders/val.extxyz ELEMENTAL_REFERENCE_MANIFEST=/tmp/e3placeholders/el.json
source "$PROJ_ROOT/examples/active_learning/env-lux/phosphorene.sh"
export PYTHONPATH="$PROJ_ROOT/src:$PROJ_ROOT"
mkdir -p "$ROOT/e3-qe-lux-inputs/convergence"
exec "$ROOT/e3-qe-lux-inputs/env/venv-host/bin/python" "$PROJ_ROOT/scripts/e3_qe_convergence.py" run --nodes "${SLURM_JOB_NUM_NODES:-1}" "$@"
