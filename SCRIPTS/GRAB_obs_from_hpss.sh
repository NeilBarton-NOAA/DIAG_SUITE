#!/bin/bash
set -xu
SCRIPT_DIR=${SCRIPT_DIR:-$(dirname "$0")}
name=${1}
source ${SCRIPT_DIR}/experiment_options.sh DUMMY DUMMY 
outdir=${TOPDIR_OBS}

file=/NCEPDEV/emc-marine/5year/Neil.Barton/DIAG/OBS/${name}.tar

mkdir -p ${outdir} && cd ${outdir}
if [[ ! -d ${outdir}/${name} ]]; then
    htar -xvf ${file}
else
    echo "${name} files already downloaded"
fi

