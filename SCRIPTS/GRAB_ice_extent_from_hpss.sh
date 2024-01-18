#!/bin/bash
set -xu
name=ice_extent
file=/NCEPDEV/emc-marine/5year/Neil.Barton/DIAG/OBS/${name}.tar
outdir=${NPB_WORKDIR}/DIAG/OBS

mkdir -p ${outdir} && cd ${outdir}
if [[ ! -d ${outdir}/${name} ]]; then
    htar -xvf ${f_get}
else
    echo "${name} files already downloaded"
fi

