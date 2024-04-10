#!/bin/bash
set -u
dtg=${1}
EXP=${2}
ENS_MEMBERS=${3}
SCRIPT_DIR=$(dirname "$0")

source ${SCRIPT_DIR}/directories.sh ${EXP} ${dtg}
source ${SCRIPT_DIR}/functions.sh

if [[ ${SRC_DIR} == *scratch* ]]; then
    echo 'FILES already on local machine'
    exit 0
fi

components=CICE
[[ ${components} == CICE ]] && f=ice.tar && dir_name=ice

if [[ ${EXP:0:2} == 'EP' ]]; then
    set -x
    local_download_dir=${TOPDIR_OUTPUT}/${EXP}/${dtg:0:8}
    hpss_file=${SRC_DIR}/${dtg:0:4}/${dtg:0:6}/${dtg:0:8}/gefs.${dtg:0:8}_${dtg:8:10}.atmos.${f} 
    FL=35 # Forecast Length is 35 days
else
    echo "SCRIPT Changed a lot, do not know"
    exit 1
    #local_dir=${outdir}/gfs.${dtg:0:8}/${DTG:8:2}/${dir_name}
    #FL=16
fi
mkdir -p ${local_download_dir} && cd ${local_download_dir}

############
# determine if needed to download
FILES_PRESENT=$( correct_n_files ${local_download_dir}/${dir_name} ${ENS_MEMBERS} ${FL})

if [[ ${FILES_PRESENT} == F ]]; then
    htar -xvf ${hpss_file}
    if (( ${?} > 0 )); then
        echo 'HTAR failed'
        exit 1
    fi
    # double check files
    FILES_PRESENT=$( correct_n_files ${local_download_dir}/${dir_name} ${ENS_MEMBERS} ${FL})
    if [[ ${FILES_PRESENT} == F ]]; then
        echo 'Download file failed, check',${local_download_dir}
        exit 1
    fi
else
    echo "${components} files already downloaded"
fi

