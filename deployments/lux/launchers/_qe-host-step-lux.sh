#!/bin/bash
# Per-task body of a pw.x step started by _qe-step-lux.sh when the AL driver runs inside an Apptainer
# image (srun --export=NONE, so nothing from the image leaks in). Runs on the compute-node host.
set -euo pipefail
PW_BIN="$1"; INPUT="$2"; WORK_DIR="$3"; THREADS="$4"; GPUS="$5"
export PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
export HOME="${HOME:-/ccs/home/$(id -un)}"
for init in /sw/lux/lmod/9.4.3/init/bash /usr/share/lmod/lmod/init/bash; do
  if ! command -v module >/dev/null 2>&1 && [[ -f "${init}" ]]; then source "${init}"; fi
done
[[ -n "${QE_MODULEPATH:-}" ]] && export MODULEPATH="${QE_MODULEPATH}"
module load "${ROCM_MODULE:-rocm/7.2.4}"
module load "${AMD_LLVM_MODULE:-amd-llvm/7.2.4}"
module load "${OPENMPI_MODULE:-openmpi/5.0.10}"
module load "${UCX_MODULE:-ucx/1.22.0}"
module load "${UCC_MODULE:-ucc/1.8.0}"
module load "${QE_MODULE:-qe/develop_omp5_76omp-lux-tuned}"
export OMP_NUM_THREADS="${THREADS}" OMP_PLACES=cores OMP_PROC_BIND=close
export OMP_TARGET_OFFLOAD="${OMP_TARGET_OFFLOAD:-DEFAULT}" OMP_STACKSIZE="${OMP_STACKSIZE:-512M}"
export QE76_GPUS_PER_NODE="${GPUS}"
cd "${WORK_DIR}"
exec qe-gpu-bind "${PW_BIN}" -i "${INPUT}"
