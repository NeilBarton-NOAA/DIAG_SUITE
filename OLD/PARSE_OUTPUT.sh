#!/bin/sh
set -u
EXP=${1:-'RETROV17'}
MODEL=${2:-'ice'}
BACKGROUND_JOB=T
export DIAG_DIR=${PWD}
source ${PWD}/MACHINE/config.sh
YAML=${DIAG_DIR}/YAMLS/eval.yaml

if [[ ${EXP} == "RTOFS" ]]; then
    directories=$(ls -d ${TOPDIR_OUTPUT}/${EXP}/????????/)
    #directories=$(ls -d ${TOPDIR_OUTPUT}/${EXP}/20250801/)
else
    directories=$(ls -d ${TOPDIR_OUTPUT}/${EXP}/*.????????/)
fi
for dir in ${directories}; do
    echo $dir
    dtg=$(basename ${dir}) && dtg=${dtg#*.}00
    f_out=${TOPDIR_OUTPUT}/${EXP}/${MODEL}_${dtg}.nc
    if [[ ! -f ${f_out} ]]; then
        echo ${f_out}
        JOB_NAME=PARSE.${EXP}.${MODEL}.${dtg}
        source ${DIAG_DIR}/MACHINE/config.sh
        if [[ ${EXP} == "RTOFS" ]]; then
            files=$( find ${dir} -name "*cice*.nc" | grep ${MODEL} | sort )
        else
            files=$( find ${dir} -name "*.nc" | grep ${MODEL} )
        fi
        ${SUBMIT} ${DIAG_DIR}/SCRIPTS/PARSE_output.py -f ${files} -o ${f_out} -y ${YAML}
        [[ ${?} > 0 ]] && echo "FATAL with SUBMIT" && exit 1
        echo "NPB check" && exit 1
    fi
done
