#!/bin/sh
# submit script for python scripts
WALLTIME="08:00:00"
#QOS="debug"
export pytools=${PWD}
#exps="beta1.1_GFS_ICs_RF SFSBeta1.X_RF SFSBeta1.X_NRT beta1.1_GFS_ICs_NRT"
exps="SFSBeta1.X_RF" # SFSBeta2_RF"
#exps="SFSBeta1.X_NRT beta1.1_GFS_ICs_NRT"

for exp in ${exps}; do
    JOB_NAME="PARSE_${exp}"
    source ${PWD}/machine/config.sh && machine_config ${PWD}
    ${SUBMIT} ${PWD}/SFS_compare.py -e ${exp} -f
done
