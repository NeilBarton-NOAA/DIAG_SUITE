#!/bin/sh
set -u
HPSS_DIR=/NCEPDEV/emc-marine/5year/Neil.Barton/URSA/beta1.1_GFS_ICs/2026040100
WORK_DIR=${NPB_WORKDIR}/RUNS/COMROOT/beta1.1_GFS_ICs
HPC_ACCOUNT=${COMPUTE_ACCOUNT} && WALLTIME="01:00:00" && NTASKS=1 

####################################
main(){
    machine_config
    files=$( hsi find ${HPSS_DIR} -name *"monthly"*".tar" 2>&1 | grep NCEPDEV | grep -v atmos )
    for f in ${files}; do
        of=${PWD}/logs_$(basename ${f}).out 
        export WORK_DIR=${WORK_DIR}
        export f=${f}
        ${SUBMIT} -J "$(basename ${f})" -o "${of}" --wrap="cd ${WORK_DIR} && htar -xvf ${f}"
    done    
}

####################################
# scrath dir based in machine
machine_config(){
    machine=$(uname -n)
    if [[ ${machine} == gaea* || ${machine} == dtn* || ${machine} == c6* ]]; then
        SUBMIT_HPSS="--mem=100G --qos=hpss --clusters=es --partition=dtn_f5_f6 --constraint=f6"
        BATCH_SYSTEM="sbatch"
    elif [[ ${machine} == u* ]]; then
        SUBMIT_HPSS="--mem=100G --partition=u1-service"
        BATCH_SYSTEM="sbatch"
    elif [[ ${machine} == clog* ]]; then
        SUBMIT_HPSS="-q dev_transfer -V --mem=5GB"
        BATCH_SYSTEM="qsub"
    else
        echo 'FATAL: MACHINE UNKNOWN'
        exit 1
    fi
    SUBMIT="${BATCH_SYSTEM} -t ${WALLTIME} -A ${HPC_ACCOUNT} -n ${NTASKS} ${SUBMIT_HPSS}"
}

main
