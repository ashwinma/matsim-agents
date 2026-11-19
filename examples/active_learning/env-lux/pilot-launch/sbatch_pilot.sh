#!/bin/bash
#SBATCH -A ven136
#SBATCH -p batch
#SBATCH -N 8
#SBATCH --gpus-per-node=8
#SBATCH --exclusive
#SBATCH -t 04:00:00
#SBATCH -J e3qe-phos-pilot
#SBATCH -o /lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval/pilot-phos-logs/pilot-%j.out
# Driver runs here (compute node 0) inside the ROCm image; geometry/LLM/QE all run from the driver.
D=/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval/pilot-phos
source $D/env.sh
export MATSIM_E3_MLIP_WORKER_PYTHON=$D/worker-python.sh
# Direct POST from compute nodes to the login-node proxy works (tested 2026-11-19); no handoff needed.
export MATSIM_VLLM_BASE_URL=http://login1:18181/v1 MATSIM_VLLM_API_KEY="$(cat $HOME/.ignite_key)"
echo "llm key length ${#MATSIM_VLLM_API_KEY} MODULEPATH length ${#MODULEPATH}"
echo "job=$SLURM_JOB_ID nodes=$SLURM_JOB_NODELIST start=$(date)"
cd $PROJ_ROOT
$D/ctr.sh python3 -u -m benchmarks.e3.qe_active_learning run --material phosphorene \
  --config examples/active_learning/e3_qe_mace_lux.yaml --approve-compute
echo "DRIVER_EXIT=$? end=$(date)"
