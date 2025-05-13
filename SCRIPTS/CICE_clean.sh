#!/bin/sh
set -eux
dtg=${1}
EXP=${2}

exit 0
SCRIPT_DIR=$(dirname "$0")
source ${SCRIPT_DIR}/experiment_options.sh ${EXP} ${dtg}
source ${SCRIPT_DIR}/functions.sh ${EXP}
source ${SCRIPT_DIR}/workflow_options.sh

src_dir=${local_ice_dir}
if [[ ${WORKFLOW} == GW ]]; then
    src_dir=${local_download_dir}/${RUN}.${dtg:0:8}/${dtg:8:10}/mem000/model/ice/history   
    [[ -d ${src_dir} ]] && rm -r ${local_download_dir}/${RUN}.${dtg:0:8}/${dtg:8:10}/mem*/model/ice/history   
    
else
    [[ -d ${src_dir} ]] && rm -r ${src_dir} 

fi

# remove files and directories
nfiles=$( ls ${src_dir}/*${dtg}.nc 2>/dev/null | wc -l ) 
if (( ${nfiles} > 0 )); then
    rm ${TOPDIR_OUTPUT}/TEMP/*${dtg}*.nc 
fi



