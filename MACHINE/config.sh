#!/bin/sh
####################################
# Local Directoriesi and 'global' variables
machine=$(uname -n)
JOB_NAME=${JOB_NAME:-hpss}
WALLTIME=${WALLTIME:-01:00:00}

BATCH_SYSTEM="sbatch"
SUBMIT_SUFFIX=""
SUBMIT_HPSS_SUFFIX=""
if [[ ${machine:0:3} == hfe || ${machine} == h*[cm]* ]]; then
    machine=hera
    export WORK_DIR=/scratch2/NCEPDEV/stmp3
elif [[ ${machine} == hercules* ]]; then
    machine=hercules
    export WORK_DIR=/work/noaa/marine
elif [[ ${machine} == gaea* || ${machine} == dtn* || ${machine} == c6* ]]; then
    machine=gaea
    export WORK_DIR=/gpfs/f6/sfs-emc/scratch
    SUBMIT_SUFFIX="--qos=normal --clusters=c6 --partition=batch"
    SUBMIT_HPSS_SUFFIX="--qos=hpss --clusters=es --partition=dtn_f5_f6 --constraint=f6"
elif [[ ${machine} == u* ]]; then
    machine=ursa
    export WORK_DIR=/scratch4/NCEPDEV/stmp
    SUBMIT_HPSS_SUFFIX="--partition=u1-service"
else
    echo 'FATAL: MACHINE UNKNOWN'
    exit 1
fi
SUBMIT="${BATCH_SYSTEM} 
    --job-name=${JOB_NAME} 
    --output=${DIAG_DIR}/logs/${JOB_NAME}.out
    --error=${DIAG_DIR}/logs/${JOB_NAME}.out
    --time=${WALLTIME} 
    --account=${HPC_ACCOUNT} 
    --ntasks=1 
    --mem=0 
    ${SUBMIT_SUFFIX}"
SUBMIT_HPSS="${SUBMIT} ${SUBMIT_HPSS_SUFFIX}"

if [[ ${BACKGROUND_JOB:-F} == T ]]; then
    SUBMIT=""
    SUBMIT_HPSS=""
fi

mkdir -p ${DIAG_DIR}/logs
export TOPDIR_OBS=${WORK_DIR}/${USER}/DIAG/OBS
export TOPDIR_OUTPUT=${WORK_DIR}/${USER}/DIAG
export TOPDIR_FIGURES=${WORK_DIR}/${USER}/FIGURES


