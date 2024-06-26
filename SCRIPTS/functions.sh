#!/bin/sh
set -u
correct_n_files () {
dir=${1}
ENS_MEMBERS=${2}
FL=${3}
FPD=${4}
MEMS=$(( ENS_MEMBERS + 1 ))
expected_files=$(( MEMS * FL * FPD )) 
nfiles=$(ls ${local_ice_dir}/*nc 2>/dev/null | wc -l )
CORRECT=F
if (( ${nfiles} >= ${expected_files} )); then
    #check size of files
    echo "Checking if Size of Files is the Same:", ${dir} , ${file_search}
    SC=$( ls -l ${dir}/${file_search} | awk '{print $5}' | sort -u | wc -l )
    if (( ${SC} == 2 )); then
        SIZE_CHECK=T
    else
        SIZE_CHECK=F
    fi
    #check number per member
    N_CHECK=T
    if (( ${ENS_MEMBERS} > 0 )); then
        n_control=$( ls ${dir}/*.?00.nc | wc -l )
        for n in $( seq 1 ${ENS_MEMBERS}); do
            mem=$(printf "%02d" ${n})
            n_mem=$( ls ${dir}/*.?${mem}.nc | wc -l )
            if (( ${n_control} != ${n_mem} )); then
                N_CHECK=F
                echo "number of member ${mem} files does not equal the number of the control member"
                echo "  N_CONTROL: ${n_control}"
                echo "  N_MEMBER: ${n_mem}"
            fi
        done
    fi
    [[ ${N_CHECK} == T ]] && [[ ${SIZE_CHECK} == T ]] && CORRECT=T
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

