#!/bin/sh
set -u
EXP=${1:-'GFSv17'}
OBS=${2:-'amsr2 osi_saf ostia sss'}
export DIAG_DIR=${PWD}
source ${DIAG_DIR}/experiment_options.sh ${EXP}
source ${DIAG_DIR}/MACHINE/config.sh

start_dtg=$(ls -d ${TOPDIR_OUTPUT}/${EXP}/${RUN}.*/ | head -n 1 | xargs basename | cut -d'.' -f2-)
end_dtg=$(ls -d ${TOPDIR_OUTPUT}/${EXP}/${RUN}.*/ | tail -n 1 | xargs basename | cut -d'.' -f2-)

for OB in ${OBS}; do
     JOB_NAME=GET.${OB}
     WALLTIME="01:00:00"
     source ${DIAG_DIR}/MACHINE/config.sh
     #SUBMIT=""
     ${SUBMIT} ${DIAG_DIR}/GRAB_OBS/grab_${OB}.sh ${start_dtg} ${end_dtg}
done

