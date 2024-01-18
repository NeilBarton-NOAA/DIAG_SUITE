#!/bin/sh
set -xu
dtg=${1}
var=${2}
topdir=${3} 
member=$(printf "%02d" ${4})

EXP=${topdir##*/}
if [[ ${MODEL} == 'GEFS' ]]; then
#if [[ ${EXP} == EP4 ]] || [[ ${EXP} == EP4a ]]; then
    dir=$( ls -d ${topdir}/${dtg:0:8}/ice/ )
elif [[ ${EXP} == HR1 ]]; then
    dir=$( ls -d ${topdir}/*.${dtg:0:8}/${dtg:8:2}/ice/ )
else
    dir=$( ls -d ${topdir}/*.${dtg:0:8}/${dtg:8:2}/model_data/ice/history )
fi

if [[ ${MODEL} == 'GEFS' ]]; then
    out_file=${topdir}/${var}_${member}_${dtg}.nc
else 
    out_file=${topdir}/${var}_${dtg}.nc
fi

area_file=$(dirname ${out_file})/cice_area.nc
if [[ ! -f ${area_file} ]]; then
    echo "making area file"
    if [[ ${MODEL} == GEFS ]]; then
        f=$(ls ${dir}/iceh*${member}.nc | tail -1)
    else
        f=$(ls ${dir}/ice[1,2]*.nc | tail -1)
    fi
    ncks -v tarea ${f} ${area_file}
    (( $? != 0 )) && exit 1
fi

if [[ -f ${out_file} ]]; then
    echo "${out_file} already made"
    echo ""
    exit 0
fi

# function to parse files
CICE_PARSE(){
in_file=${1}
out_tau_file=${2}
var=${3}
if [[ ${MODEL} == 'GEFS' ]]; then
    temp_file=$( dirname ${in_file})/CICE_VARS_IC_M${member}.nc
else
    temp_file=$( dirname ${in_file})/CICE_VARS_IC.nc
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

############
#   IC file
file_tau_list=""
if [[ ${MODEL} != 'GEFS' ]]; then
    # GEFS IC is also written out
    in_file=$(ls ${dir}/iceic*nc)
    if [[ -z ${in_file} ]]; then
        echo "ic file not found in:" ${dir}
        exit 1
    fi
    tau=000
    out_tau_file=$(dirname ${in_file})/CICE_${dtg}_M${member}_${tau}.nc
    CICE_PARSE ${in_file} ${out_tau_file} ${var}
    (( $? != 0 )) && exit 1
    file_tau_list=${file_tau_list}' '${out_tau_file}
fi
############
# tau files
if [[ ${MODEL} == 'GEFS' ]]; then
    files=$(ls ${dir}/iceh*${member}.nc)
else
    files=$(ls ${dir}/ice[1,2]*.nc)
fi

for f in ${files}; do
    if [[ ${MODEL} == 'GEFS' ]]; then
        f_name=$(basename ${f}) 
        f_dtg=${f_name:5:4}${f_name:10:2}${f_name:13:2}00
    else
        f_dtg=$(basename ${f}) && f_dtg=${f_dtg:3:10}
    fi
    tau=$( ${SCRIPT_DIR}/CALC_tau.sh ${dtg} ${f_dtg}) && tau=$(printf "%03d" $tau)
    out_tau_file=$(dirname ${f})/CICE_${dtg}_M${member}_${tau}.nc
    CICE_PARSE ${f} ${out_tau_file} ${var}
    (( $? != 0 )) && exit 1
    file_tau_list=${file_tau_list}' '${out_tau_file}
done

ncecat -u tau ${file_tau_list} ${out_file}
(( $? != 0 )) && exit 1
rm ${file_tau_list}

echo "CREATED:" ${out_file}
echo " "

