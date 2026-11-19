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

# Container mode: the AL driver may run inside an Apptainer image (Lux: ROCm torch lives only in the
# image) with the host srun bound in. Modules and qe-gpu-bind then belong to the compute-node host, not
# the image, so they are loaded by _qe-host-step-lux.sh inside the srun step instead of here.
IN_CONTAINER=0
if [[ -n "${APPTAINER_CONTAINER:-}${SINGULARITY_CONTAINER:-}" ]]; then IN_CONTAINER=1; fi

if [[ "${IN_CONTAINER}" == 0 ]]; then
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
fi

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

# qe-gpu-bind (qe/develop_omp5_76omp-lux-tuned) computes its OWN GPU
# assignment -- ROCR_VISIBLE_DEVICES = local_rank mod QE76_GPUS_PER_NODE
# (default 8) -- and unconditionally overwrites/unsets any HIP_*/ROCR_*
# device-mask env vars set before it runs (confirmed by reading
# $QE76_ROOT/bin/qe-gpu-bind in full). It does NOT accept an explicit
# device list or offset, so a pre-set ROCR_VISIBLE_DEVICES="${MATSIM_DEVICE_MASK}"
# (the Frontier-script pattern) is silently discarded. The only lever this
# tool exposes is QE76_GPUS_PER_NODE, which narrows its modulo to the first
# N node-local GPU indices (0..N-1) -- it cannot target an arbitrary/offset
# subset such as "4,5,6,7". We therefore honour MATSIM_DEVICE_MASK /
# MATSIM_DEVICES_PER_NODE only in the two cases this tool can actually
# support, and fail loudly rather than silently binding to the wrong GPUs
# otherwise:
#   - full node (placement uses every node GPU): --exclusive, QE76_GPUS_PER_NODE
#     = total node devices (matches qe-gpu-bind's own validated AUSURF112
#     usage pattern, where the default 8 is correct because the step owns
#     the whole node).
#   - zero-based contiguous subset (e.g. "0,1,2,3" out of 8): --overlap +
#     --gpus-per-node=<subset size>, relying on Slurm/cgroup GRES isolation
#     to restrict which physical GPUs this step's /sys/class/kfd view
#     contains, with QE76_GPUS_PER_NODE set to the subset size so
#     qe-gpu-bind's modulo lands inside it. NOT independently validated on
#     Lux for a live multi-pool-sharing run -- depends on Slurm's gres/gpu
#     cgroup enforcement actually narrowing kfd topology visibility per
#     step, which this pass only confirmed by reading documentation/source,
#     not by running two overlapping steps on one node.
# A non-zero-based or non-contiguous mask (e.g. "4,5,6,7") cannot be
# honoured by this tool at all; such a placement is rejected below instead
# of silently running on the wrong GPUs.
STEP_GPUS="${GPUS_PER_NODE}"
STEP_SHARE=(--exclusive)
STEP_GPU_FLAGS=()
if [[ -n "${MATSIM_DEVICE_MASK:-}" && -n "${MATSIM_NODE_DEVICES:-}" \
      && "${STEP_GPUS}" != "${MATSIM_NODE_DEVICES}" ]]; then
  EXPECTED_MASK=$(seq -s, 0 $(( STEP_GPUS - 1 )))
  if [[ "${MATSIM_DEVICE_MASK}" != "${EXPECTED_MASK}" ]]; then
    echo "[qe-step] FATAL: MATSIM_DEVICE_MASK=${MATSIM_DEVICE_MASK} is not the zero-based contiguous block (${EXPECTED_MASK}) qe-gpu-bind requires. qe-gpu-bind computes ROCR_VISIBLE_DEVICES = local_rank mod QE76_GPUS_PER_NODE internally and has no device-offset/explicit-list override -- it cannot be pointed at an arbitrary GPU subset. Either give this pool a whole node, a zero-based GPU subset, or ask the qe-gpu-bind maintainer (Quentarius Moore, AMD) for an offset/list option." >&2
    exit 3
  fi
  STEP_SHARE=(--overlap)
  STEP_GPU_FLAGS=(--gpus-per-node="${STEP_GPUS}")
fi
export QE76_GPUS_PER_NODE="${STEP_GPUS}"

# qe-gpu-bind is REQUIRED for correct GPU dispatch under this module: running
# pw.x bare under lux-tuned measured 593s vs 43s with the wrapper on a 1-node
# smoke test (same input/output). --cpu-bind=none + --mpi=pmix are the
# validated flags for the 1- and 2-node AUSURF112 benchmark; --gpu-bind is
# deliberately NOT set here, since qe-gpu-bind itself owns GPU binding.
#
# Open MPI 5.0.10 on Lux is a debug build: every converged run we've seen
# prints "JOB DONE." and writes correct output, then exits 134 from an
# internal MPI_Finalize check (confirmed in `module show
# qe/develop_omp5_76omp-lux-tuned`'s help text). This script still execs
# srun directly and lets pw.x's real exit code (including that 134)
# propagate untouched, per spec -- callers on Lux must treat "JOB DONE." in
# the output as the convergence signal, not a zero exit code.
if [[ "${IN_CONTAINER}" == 1 ]]; then
  HOST_STEP="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_qe-host-step-lux.sh"
  echo "[qe-step] (container) srun ${STEP_SHARE[*]} ${STEP_GPU_FLAGS[*]} -N ${NNODES} --ntasks-per-node=${RANKS_PER_NODE}" \
    "-c ${THREADS_PER_RANK} --export=NONE ${HOST_STEP} ${PW_BIN} ${INPUT}"
  exec srun \
    "${STEP_SHARE[@]}" \
    "${STEP_GPU_FLAGS[@]}" \
    "${NODE_ARGS[@]}" \
    -N "${NNODES}" \
    --ntasks-per-node="${RANKS_PER_NODE}" \
    -c "${THREADS_PER_RANK}" \
    --cpu-bind=none \
    --mpi=pmix \
    --export=NONE \
    /usr/bin/env "QE_MODULEPATH=${MODULEPATH:-}" /bin/bash "${HOST_STEP}" "${PW_BIN}" "${INPUT}" "${WORK_DIR}" "${THREADS_PER_RANK}" "${QE76_GPUS_PER_NODE}"
fi

echo "[qe-step] srun ${STEP_SHARE[*]} ${STEP_GPU_FLAGS[*]} -N ${NNODES} --ntasks-per-node=${RANKS_PER_NODE}" \
  "-c ${THREADS_PER_RANK} --cpu-bind=none --mpi=pmix qe-gpu-bind ${PW_BIN} -i ${INPUT}"
exec srun \
  "${STEP_SHARE[@]}" \
  "${STEP_GPU_FLAGS[@]}" \
  "${NODE_ARGS[@]}" \
  -N "${NNODES}" \
  --ntasks-per-node="${RANKS_PER_NODE}" \
  -c "${THREADS_PER_RANK}" \
  --cpu-bind=none \
  --mpi=pmix \
  qe-gpu-bind "${PW_BIN}" -i "${INPUT}"
