#!/bin/bash
# One 1-node job per manifest entry. usage:
#   sbatch -t 06:00:00 --array=0-12%10 -J qual-long scripts/sbatch_e3_qe_qualification.sh long
#   sbatch -t 02:00:00 --array=0-23%14 -J qual-short scripts/sbatch_e3_qe_qualification.sh short
#SBATCH -A ven136
#SBATCH -p batch
#SBATCH -N 1
#SBATCH --exclusive
#SBATCH --gpus-per-node=8
#SBATCH -o /lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval/e3-qe-lux-inputs/logs/%x-%A_%a.out
set -uo pipefail
ROOT=/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval
exec "$ROOT/e3-qe-lux-inputs/env/venv-host/bin/python" "$ROOT/wt-qe-qual/scripts/e3_qe_label_qualification.py" task "$SLURM_ARRAY_TASK_ID" "$1"
