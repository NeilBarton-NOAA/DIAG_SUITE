#!/bin/sh
set -u

cice_var_name () {
f=${1}
v=${2}
var=$(ncdump -h ${f} | grep ${v}_ | grep long_name | awk '{print $1}')
echo ${var%%:*}
}

correct_n_files () {
dir=${1}
# no check for ensembles at this point
CORRECT=F
nfiles=$(ls ${local_ice_dir}/*nc | grep -v '.ic.nc' 2>/dev/null | wc -l )
if (( ${nfiles} > 0 )); then
    SIZES=$( ls -l ${local_ice_dir}/*nc | grep -v '.ic.nc' | awk '{print $5}' | sort -u | wc -l )
    if (( ${SIZES} == 1 )); then
        CORRECT=T
    fi
fi
echo ${CORRECT}
}

