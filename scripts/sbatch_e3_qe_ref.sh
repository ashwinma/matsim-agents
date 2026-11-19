#!/bin/bash
# usage: sbatch -J name -t 04:00:00 scripts/sbatch_e3_qe_ref.sh <material/frame/name>
#SBATCH -A ven136
#SBATCH -p batch
#SBATCH -N 1
#SBATCH --exclusive
#SBATCH --gpus-per-node=8
#SBATCH -o /lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval/e3-qe-lux-inputs/logs/%x-%j.out
set -uo pipefail
ROOT=/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval
exec "$ROOT/e3-qe-lux-inputs/env/venv-host/bin/python" "$ROOT/wt-qe-qual/scripts/e3_qe_ref_sweep.py" task "$1"
