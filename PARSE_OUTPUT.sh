#!/bin/sh
set -u
EXP=${1}
MODEL=${2:-'ice'}

source ${PWD}/experiment_options.sh ${EXP} ${MODEL}
source ${PWD}/MACHINE/config.sh

if [[ ${MODEL} == 'ice' ]]; then
    vars="aice hi sst sss hs Tsfc albsni meltt meltb"
fi

directories=$(ls -d ${TOPDIR_OUTPUT}/${EXP}/${RUN}.*/)
for dir in ${directories}; do
    dtg=$(basename ${dir}) && dtg=${dtg#*.}00
    f_out=${TOPDIR_OUTPUT}/${EXP}/${MODEL}_${dtg}.nc
    if [[ ! -f ${f_out} ]]; then
        echo ${f_out}
        JOB_NAME=PARSE.${EXP}.${MODEL}.${dtg}
        source ${DIAG_DIR}/MACHINE/config.sh
        files=$( find ${dir}/00/ -name "*.nc" | grep ${MODEL} )
        ${SUBMIT} ${DIAG_DIR}/SCRIPTS/PARSE_output.py -f ${files} -m ${MODEL} -v ${vars} -o ${f_out}
    fi
done
