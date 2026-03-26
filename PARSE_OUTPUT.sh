#!/bin/sh
set -u
EXP=${1:-'RETROV17'}
MODEL=${2:-'ice'}
BACKGROUND_JOB=F
export DIAG_DIR=${PWD}
source ${PWD}/MACHINE/config.sh
YAML=${DIAG_DIR}/YAMLS/eval.yaml

directories=$(ls -d ${TOPDIR_OUTPUT}/${EXP}/*.????????/)
for dir in ${directories}; do
    dtg=$(basename ${dir}) && dtg=${dtg#*.}00
    f_out=${TOPDIR_OUTPUT}/${EXP}/${MODEL}_${dtg}.nc
    if [[ ! -f ${f_out} ]]; then
        echo ${f_out}
        JOB_NAME=PARSE.${EXP}.${MODEL}.${dtg}
        source ${DIAG_DIR}/MACHINE/config.sh
        files=$( find ${dir}/00/ -name "*.nc" | grep ${MODEL} )
        ${SUBMIT} ${DIAG_DIR}/SCRIPTS/PARSE_output.py -f ${files} -o ${f_out} -y ${YAML}
        [[ ${?} > 0 ]] && echo "FATAL with SUBMIT" && exit 1
        #echo "NPB check" && exit 1
    fi
done
