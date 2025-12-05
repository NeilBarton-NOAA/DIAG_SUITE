#!/bin/sh
set -u
EXP=${1}
MODEL=${2:-'ice'}

DIAG_DIR=${PWD}
source ${DIAG_DIR}/experiment_options.sh ${EXP} ${MODEL}
source ${DIAG_DIR}/SCRIPTS/functions.sh
source ${DIAG_DIR}/MACHINE/config.sh
        
EXPDIR=${TOPDIR_OUTPUT}/${EXP} 
mkdir -p ${EXPDIR} && cd ${EXPDIR}

########################
# get all tar files that are available 
files=$( hsi -q find ${HPSS_DIR}/*00 -name ${HPSS_FILE} 2>&1 | grep NCEPDEV )
for f in ${files}; do
    dtg=$( echo "${f}" | awk -F'/' '{print $(NF-1)}' )
    local_dir=${TOPDIR_OUTPUT}/${EXP}/${RUN}.${dtg:0:8}/${dtg:8:10}/model/${MODEL}/history   
    #echo "LOOKING FOR ALREADY DOWNLOADED FILES IN: ${local_dir}"
    FILES_PRESENT=$( correct_n_files "${local_dir}")
    f_out=${TOPDIR_OUTPUT}/${EXP}/${MODEL}_${dtg}.nc
    if [[ ${FILES_PRESENT} == F && ! -f ${f_out} ]]; then
        echo "  downloading ${f}"
        JOB_NAME=GET.${EXP}.$(basename ${f%.tar}).${dtg}
        source ${DIAG_DIR}/MACHINE/config.sh
        ${SUBMIT_HPSS} htar -xvf ${f}
    fi
done
