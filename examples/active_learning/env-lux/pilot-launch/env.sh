# source me. Pilot env: phosphorene, fixed 7x5x1 mesh (consistent with validation-phosphorene.extxyz)
ROOT=/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval
I=$ROOT/e3-qe-lux-inputs
export PROJ_ROOT=$ROOT/matsim-agents-pilot-phos MACE_CHECKPOINT=$HOME/.cache/mace/maceomat0mediummodel
export PW_BIN=/lustre/orion/ven136/proj-shared/qe/76omp-bf7acca2/bin/pw.x
export E3_QE_LUX_ROOT=$ROOT/pilot-phos/runs
export E3_QE_VALIDATION_SET=$I/validation-phosphorene.extxyz
export ELEMENTAL_REFERENCE_MANIFEST=$I/elemental/manifests/phosphorene/elemental-references.json
source $PROJ_ROOT/examples/active_learning/env-lux/phosphorene.sh
export E3_QE_VALIDATION_SET=$I/validation-phosphorene.extxyz ELEMENTAL_REFERENCE_MANIFEST=$I/elemental/manifests/phosphorene/elemental-references.json
export MATSIM_E3_OBJECTIVES_PATH=$PROJ_ROOT/benchmarks/e3/scientific-objectives-lux.yaml
export MATSIM_E3_MLIP_STRUCTURES_PER_ROUND=64 MATSIM_E3_GPUS_PER_NODE=${MATSIM_E3_GPUS_PER_NODE:-8}
export PYTHONPATH=$PROJ_ROOT/src:$PROJ_ROOT
