#!/bin/sh
set -eux
dtg=${1}
var=${2}
EXP=${3}

SCRIPT_DIR=$(dirname "$0")
source ${SCRIPT_DIR}/experiment_options.sh ${EXP} ${dtg}
source ${SCRIPT_DIR}/functions.sh ${EXP}
source ${SCRIPT_DIR}/workflow_options.sh

src_dir=${local_ice_dir}
[[ ${WORKFLOW} == GW ]] && src_dir=${local_download_dir}/${RUN}.${dtg:0:8}/${dtg:8:10}/mem${MEM}/model/ice/history   

f=$( ls ${src_dir}/*nc | head -n 1 )
cice_var=$(cice_var_name ${f} ${var})
# echo need ensmbles
${SCRIPT_DIR}/PYTHON_TOOLS/CICE_parse.py -v ${cice_var} -e ${EXP} -d ${src_dir}



