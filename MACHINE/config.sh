#!/bin/sh
####################################
# Local Directoriesi and 'global' variables
machine=$(uname -n)
JOB_NAME=${JOB_NAME:-hpss}
WALLTIME=${WALLTIME:-01:00:00}
if [[ ${machine:0:3} == hfe || ${machine} == h*[cm]* ]]; then
    WORK_DIR=/scratch2/NCEPDEV/stmp3

elif [[ ${machine} == hercules* ]]; then
    WORK_DIR=/work/noaa/marine

elif [[ ${machine} == gaea* || ${machine} == dtn* || ${machine} == c6* ]]; then
    WORK_DIR=/gpfs/f6/sfs-emc/scratch
    SUBMIT="sbatch --job-name=${JOB_NAME} 
                 --output=${DIAG_DIR}/logs/${JOB_NAME}.out
                 --error=${DIAG_DIR}/logs/${JOB_NAME}.out
                 --time=${WALLTIME} 
                 --account=${HPC_ACCOUNT} --qos=normal
                 --ntasks=1 --mem=0
                 --clusters=c6 --partition=batch"
    SUBMIT_HPSS="sbatch --job-name=${JOB_NAME} 
                 --output=${DIAG_DIR}/logs/${JOB_NAME}.out
                 --error=${DIAG_DIR}/logs/${JOB_NAME}.out
                 --time=${WALLTIME} 
                 --account=${HPC_ACCOUNT} --qos=hpss 
                 --ntasks=1 --mem=0
                 --clusters=es --partition=dtn_f5_f6 --constraint=f6"
else
    echo 'FATAL: MACHINE UNKNOWN'
    exit 1
fi

if [[ ${BACKGROUND_JOB:-F} == T ]]; then
    SUBMIT=""
    SUBMIT_HPSS=""
fi

mkdir -p ${DIAG_DIR}/logs
export TOPDIR_OBS=${WORK_DIR}/${USER}/DIAG/OBS
export TOPDIR_OUTPUT=${WORK_DIR}/${USER}/DIAG
export TOPDIR_FIGURES=${WORK_DIR}/${USER}/FIGURES


