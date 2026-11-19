#!/bin/bash
# Run a command inside the ROCm/MACE Apptainer image with host srun + munge bridged in
# (driver needs torch-ROCm; srun/modules live on the host). usage: ctr.sh python3 -m ...
ROOT=/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval
P=$ROOT/pilot-phos
MIOPEN=/tmp/miopen-pilot-${SLURM_JOB_ID:-x}
exec apptainer exec --rocm --overlay $ROOT/scratch-leftovers/mace-overlay.img:ro \
  --bind /lustre/orion/ven136 --bind /usr/bin/srun:/usr/bin/srun --bind /usr/lib64/slurm:/usr/lib64/slurm --bind /run/munge \
  --env LD_LIBRARY_PATH=/usr/lib64/slurm:$P/hostlibs \
  --env SLURM_CONF=$P/slurm-etc/slurm.conf \
  --env PYTHONPATH=/opt/mace-pkgs:$ROOT/matsim-agents-pilot-phos/src:$ROOT/matsim-agents-pilot-phos \
  --env TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 --env MIOPEN_USER_DB_PATH=$MIOPEN --env MIOPEN_CUSTOM_CACHE_DIR=$MIOPEN \
  /lustre/orion/ven136/proj-shared/ashwinaji/ai4science/images/pytorch_rocm7.14.1_ubuntu24.04_py3.12_pytorch_release_2.12.0.sif "$@"
