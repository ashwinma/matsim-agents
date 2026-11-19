#!/bin/bash
# Host-side "python" for srun-launched E3 geometry workers (MATSIM_E3_MLIP_WORKER_PYTHON).
exec /lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval/pilot-phos/ctr.sh python3 "$@"
