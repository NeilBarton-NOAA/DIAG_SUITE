#!/bin/bash
set -xu
SCRIPT_DIR=${SCRIPT_DIR:-$(dirname "$0")}
source ${SCRIPT_DIR}/directories.sh
outdir=${TOPDIR_OBS}

name=ice_extent
file=/NCEPDEV/emc-marine/5year/Neil.Barton/DIAG/OBS/${name}.tar

mkdir -p ${outdir} && cd ${outdir}
if [[ ! -d ${outdir}/${name} ]]; then
    htar -xvf ${f_get}
else
    echo "${name} files already downloaded"
fi

