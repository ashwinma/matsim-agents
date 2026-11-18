#!/bin/bash
# CPU-build comparison: qe/7.13.0-afar-23.2.1 pw.x (no omp-target offload) on one LiFePO4 qualification frame.
# usage: sbatch -J qual-cpu scripts/sbatch_e3_qe_qualification_cpu.sh <run_dir_with_pw.in>
#SBATCH -A ven136
#SBATCH -p batch
#SBATCH -N 1
#SBATCH --exclusive
#SBATCH -t 03:00:00
#SBATCH -o /lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval/e3-qe-lux-inputs/logs/%x-%j.out
set -uo pipefail
D="$1"; cd "$D"
source /usr/share/lmod/lmod/init/bash 2>/dev/null || true
module load qe/7.13.0-afar-23.2.1
unset LD_PRELOAD PYTHONPATH
export OMP_NUM_THREADS=2
srun -N1 -n64 -c2 --cpu-bind=cores --mpi=pmix pw.x -nk 4 -in pw.in > pw.out 2>&1
rm -rf tmp core.*
