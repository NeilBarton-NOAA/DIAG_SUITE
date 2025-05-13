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

# function to parse files
CICE_PARSE(){
in_file=${1}
out_tau_file=${2}
v=${3}
ENS_MEMBERS=${4}
mkdir -p $( dirname ${out_tau_file} )
if (( ${ENS_MEMBERS} > 0 )); then
    temp_file=$( dirname ${out_tau_file})/CICE_${v}_M${MEM}.nc
else
    temp_file=$( dirname ${out_tau_file})/CICE_${v}.nc
fi
tau=${out_tau_file##*${MEM}_} && tau=${tau%%.nc*}
if [[ ! -f ${out_tau_file} ]]; then
    [[ -f ${temp_file} ]] && rm ${temp_file}
    ncks -v ${v} ${in_file} ${temp_file}
    (( $? != 0 )) && exit 1
    ncap2 -s "tau=${tau}" -O ${temp_file} ${out_tau_file}_TAREA
    (( $? != 0 )) && exit 1
    rm ${temp_file}
    ncks -C -O -x -v tarea ${out_tau_file}_TAREA ${out_tau_file}
    (( $? != 0 )) && exit 1
    rm ${out_tau_file}_TAREA
    ncrename -v ${v},${v%%_*} ${out_tau_file}
fi
echo "in file:" ${in_file}
echo "CREATED:" ${out_tau_file}
}

