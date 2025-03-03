#!/bin/bash
set -xu
dtg=${1}
EXP=${2}
ENS_MEMBERS=${3}
SCRIPT_DIR=$(dirname "$0")
source ${SCRIPT_DIR}/experiment_options.sh ${EXP} ${dtg}
source ${SCRIPT_DIR}/functions.sh
source ${SCRIPT_DIR}/workflow_options.sh

if [[ ${SRC_DIR} == "local" ]]; then
    echo 'FILES already on local machine'
    exit 0
fi

mkdir -p ${local_download_dir} && cd ${local_download_dir}

############
# determine if needed to download
FILES_PRESENT=$( correct_n_files "${local_ice_dir}" ${ENS_MEMBERS})

if [[ ${FILES_PRESENT} == F ]]; then
    echo ${hpss_file}
    htar -xvf ${hpss_file}
    if (( ${?} > 0 )); then
        echo 'HTAR failed'
        exit 1
    fi
    # double check files
    FILES_PRESENT=$( correct_n_files "${local_ice_dir}" ${ENS_MEMBERS})
    if [[ ${FILES_PRESENT} == F ]]; then
        echo 'Download file failed, check',${local_ice_dir}
        exit 1
    fi
else
    echo "files already downloaded"
fi
