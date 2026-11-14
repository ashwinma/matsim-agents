#!/bin/bash
# =============================================================================
# _qe-step-lux.sh
#
# Inner-step launcher for ONE Quantum ESPRESSO pw.x single-point on OLCF Lux
# (AMD MI355X / gfx950). Called by the active-learning Python driver
# (matsim_agents.backends.dft.qe.QEBackend) via:
#
#   bash _qe-step-lux.sh <work_dir> <pw_bin> <input_file> \
#                        <nodes> <ranks_per_node> <threads_per_rank>
#
# DRAFT, not yet validated end-to-end against a real E3 structure -- see
# .cursor/skills/ai4science-material-science/reference/quantum-espresso-lux.md
# in ai4science-studio for the full set of Lux QE gotchas this was built
# against (Lux is not a Cray PE system: no PrgEnv/ftn/cc/cray-mpich).
#
# Unlike the earlier (CPU-only) qe/7.13.0-afar-23.2.1 build documented in that
# reference doc, this targets qe/develop_omp5_76omp-lux-tuned -- the build
# with genuine multi-node-validated `!$omp target` GPU offload (2-node
# AUSURF112 benchmark matching reference energy; credit Quentarius Moore,
# AMD). That build's correctness/perf depends on wrapping pw.x with its
# qe-gpu-bind helper, which this script does; running pw.x bare under this
# module has NOT been validated and should not be assumed equivalent.
# =============================================================================

set -euo pipefail

if [[ $# -lt 6 ]]; then
  echo "Usage: $0 <work_dir> <pw_bin> <input_file> <nodes> <ranks_per_node> <threads_per_rank>" >&2
  exit 2
fi

WORK_DIR="$1"
PW_BIN="$2"
INPUT="$3"
NNODES="$4"
RANKS_PER_NODE="$5"
THREADS_PER_RANK="$6"
TOTAL_RANKS=$(( NNODES * RANKS_PER_NODE ))
# Devices per node come from the placement; several ranks may share one device.
GPUS_PER_NODE="${MATSIM_DEVICES_PER_NODE:-$RANKS_PER_NODE}"

[[ -d "${WORK_DIR}" ]] || { echo "work_dir not a directory: ${WORK_DIR}" >&2; exit 2; }
[[ -x "${PW_BIN}"   ]] || { echo "pw.x not executable: ${PW_BIN}" >&2; exit 2; }
[[ -f "${INPUT}"    ]] || { echo "input file missing: ${INPUT}" >&2; exit 2; }

# ── Module load for the QE build's toolchain ────────────────────────────────
# Lux is a plain Lmod system, not Cray PE: no `module reset`/PrgEnv swap
# needed, just load the dependency chain the lux-tuned module was built
# against (confirmed via `module show qe/develop_omp5_76omp-lux-tuned`).
if ! command -v module >/dev/null 2>&1 && [[ -f /usr/share/lmod/lmod/init/bash ]]; then
  # shellcheck disable=SC1091
  source /usr/share/lmod/lmod/init/bash
fi

module load "${ROCM_MODULE:-rocm/7.2.4}"
module load "${AMD_LLVM_MODULE:-amd-llvm/7.2.4}"
module load "${OPENMPI_MODULE:-openmpi/5.0.10}"
module load "${UCX_MODULE:-ucx/1.22.0}"
module load "${UCC_MODULE:-ucc/1.8.0}"
module load "${QE_MODULE:-qe/develop_omp5_76omp-lux-tuned}"

command -v qe-gpu-bind >/dev/null 2>&1 || {
  echo "qe-gpu-bind not found on PATH after loading ${QE_MODULE:-qe/develop_omp5_76omp-lux-tuned}" >&2
  exit 2
}

# Strip env vars set by the Python venv/Apptainer env that would perturb the
# QE launch (same rationale as _qe-step-perlmutter.sh / _qe-step-frontier.sh).
unset LD_PRELOAD || true
unset PYTHONPATH || true

# ── QE runtime tuning ────────────────────────────────────────────────────────
export OMP_NUM_THREADS="${THREADS_PER_RANK}"
export OMP_PLACES="cores"
export OMP_PROC_BIND="close"
export OMP_TARGET_OFFLOAD="${OMP_TARGET_OFFLOAD:-DEFAULT}"
export OMP_STACKSIZE="${OMP_STACKSIZE:-512M}"

cd "${WORK_DIR}"

echo "[qe-step] $(date) host=$(hostname) work_dir=${WORK_DIR}"
NODE_ARGS=()
if [[ -n "${MATSIM_ASSIGNED_NODES:-}" ]]; then
  NODE_ARGS=(--nodelist "${MATSIM_ASSIGNED_NODES}")
fi
echo "[qe-step] assigned_nodes=${MATSIM_ASSIGNED_NODES:-scheduler-selected}"

# Slurm picks which GPUs a step receives, so a GPU count alone cannot honour
# the placement's device indices. When the placement uses only some of the
# node's GPUs, take them all for the step and expose only the placed ones
# inside it via ROCR_VISIBLE_DEVICES (same pattern as _qe-step-frontier.sh).
STEP_GPUS="${GPUS_PER_NODE}"
STEP_ENV=()
STEP_SHARE=(--exclusive)
if [[ -n "${MATSIM_DEVICE_MASK:-}" && -n "${MATSIM_NODE_DEVICES:-}" \
      && "${STEP_GPUS}" != "${MATSIM_NODE_DEVICES}" ]]; then
  STEP_SHARE=(--overlap)
  STEP_ENV=(env -u HIP_VISIBLE_DEVICES "ROCR_VISIBLE_DEVICES=${MATSIM_DEVICE_MASK}")
fi

# qe-gpu-bind is REQUIRED for correct GPU dispatch under this module: running
# pw.x bare under lux-tuned measured 593s vs 43s with the wrapper on a 1-node
# smoke test (same input/output). --cpu-bind=none + --mpi=pmix are the
# validated flags for the 1- and 2-node AUSURF112 benchmark; --gpu-bind is
# deliberately NOT set here, since qe-gpu-bind itself owns GPU binding.
echo "[qe-step] srun ${STEP_SHARE[*]} -N ${NNODES} --ntasks-per-node=${RANKS_PER_NODE}" \
  "-c ${THREADS_PER_RANK} --cpu-bind=none --mpi=pmix ${STEP_ENV[*]} qe-gpu-bind ${PW_BIN} -i ${INPUT}"
exec srun \
  "${STEP_SHARE[@]}" \
  "${NODE_ARGS[@]}" \
  -N "${NNODES}" \
  --ntasks-per-node="${RANKS_PER_NODE}" \
  -c "${THREADS_PER_RANK}" \
  --cpu-bind=none \
  --mpi=pmix \
  "${STEP_ENV[@]}" \
  qe-gpu-bind "${PW_BIN}" -i "${INPUT}"
