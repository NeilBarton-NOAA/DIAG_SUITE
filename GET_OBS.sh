#!/bin/sh
set -u
EXP=${1:-'RETROV17'}
OBS=${2:-'osi_saf'}
export DIAG_DIR=${PWD}
source ${DIAG_DIR}/MACHINE/config.sh

start_dtg=$(ls ${TOPDIR_OUTPUT}/${EXP}/ice*nc | head -n 1 | xargs basename | grep -oP '(?<=_)\d{8}' )
end_dtg=$(ls ${TOPDIR_OUTPUT}/${EXP}/ice*nc | tail -n 1 | xargs basename | grep -oP '(?<=_)\d{8}' )

for OB in ${OBS}; do
    JOB_NAME=GET.${OB}
    BACKGROUND_JOB=T
    WALLTIME="01:00:00"
    source ${DIAG_DIR}/MACHINE/config.sh
    ${SUBMIT_HPSS} ${DIAG_DIR}/SCRIPTS/obs_download/grab_${OB}.sh ${start_dtg} ${end_dtg}
    [[ ${?} > 0 ]] && echo "FATAL with SUBMIT" && exit 1
done

