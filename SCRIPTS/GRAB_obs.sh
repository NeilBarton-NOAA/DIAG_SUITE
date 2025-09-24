#!/bin/bash
set -u
SCRIPT_DIR=${SCRIPT_DIR:-$(dirname "$0")}
DTG=${1}
OBS=${2}
export TOPDIR_OBS=${NPB_WORKDIR}/DIAG/OBS
export outdir=${TOPDIR_OBS}

for ob in ${OBS}; do
    echo $ob
    f=$( ls ${SCRIPT_DIR}/GRAB_OBS/grab_${ob}.* ) 
    ${f} ${DTG} ${outdir}
done
echo "NPB"
exit 1
#file=/NCEPDEV/emc-marine/5year/Neil.Barton/DIAG/OBS/${name}.tar
#mkdir -p ${outdir} && cd ${outdir}
#if [[ ! -d ${outdir}/${name} ]]; then
#    htar -xvf ${file}
#else
#    echo "${name} files already downloaded"
#fi

