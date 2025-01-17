#!/bin/sh
set -u
correct_n_files () {
dir=${1}
ENS_MEMBERS=${2}
MEMS=$(( ENS_MEMBERS + 1 ))
CORRECT=F
nfiles=$(ls ${local_ice_dir}/*nc 2>/dev/null | wc -l )
EVEN_FILES=$(( ${nfiles} % ${MEMS} ))
#FPD=$(( ${nfiles} / ${MEMS} ))
if (( ${nfiles} > 0 )); then
    SIZES=$( ls -l ${local_ice_dir}/*nc | awk '{print $5}' | sort -u | wc -l )
    if (( ${SIZES} == 1 && ${EVEN_FILES} == 0 )); then
        CORRECT=T
    fi
fi
echo ${CORRECT}
}

# function to parse files
CICE_PARSE(){
in_file=${1}
out_tau_file=${2}
var=${3}
ENS_MEMBERS=${4}
mkdir -p $( dirname ${out_tau_file} )
if (( ${ENS_MEMBERS} > 0 )); then
    temp_file=$( dirname ${out_tau_file})/CICE_VARS_IC_M${member}.nc
else
    temp_file=$( dirname ${out_tau_file})/CICE_VARS_IC.nc
fi
tau=${out_tau_file: -6:3}
if [[ ! -f ${out_tau_file} ]]; then
    [[ -f ${temp_file} ]] && rm ${temp_file}
    ncks -v ${var} ${in_file} ${temp_file}
    (( $? != 0 )) && exit 1
    ncap2 -s "tau=$tau" -O ${temp_file} ${out_tau_file}_TAREA
    (( $? != 0 )) && exit 1
    rm ${temp_file}
    ncks -C -O -x -v tarea ${out_tau_file}_TAREA ${out_tau_file}
    (( $? != 0 )) && exit 1
    rm ${out_tau_file}_TAREA
fi
echo "in file:" ${in_file}
echo "CREATED:" ${out_tau_file}
}

