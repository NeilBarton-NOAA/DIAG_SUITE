#!/bin/sh
set -xu
dtg=${1}
var=${2}
EXP=${3}
member=$(printf "%02d" ${4})
MODEL=${MODEL:-'GEFS'}

SCRIPT_DIR=$(dirname "$0")
source ${SCRIPT_DIR}/directories.sh ${EXP}
source ${SCRIPT_DIR}/functions.sh ${EXP}

if [[ ${SRC_DIR} == *scratch* ]]; then
    src_dir=${SRC_DIR}
else
    if [[ ${MODEL} == 'GEFS' ]]; then
        src_dir=$( ls -d ${TOPDIR_OUTPUT}/${EXP}/${dtg:0:8}/ice/ )
    elif [[ ${EXP} == HR1 ]] ; then
        src_dir=$( ls -d ${TOPDIR_OUTPUT}/${EXP}/*.${dtg:0:8}/${dtg:8:2}/ice/ )
    else
        src_dir=$( ls -d ${TOPDIR_OUTPUT}/*.${dtg:0:8}/${dtg:8:2}/model_data/ice/history )
    fi
fi

if [[ ${MODEL} == 'GEFS' ]]; then
    out_file=${TOPDIR_OUTPUT}/${EXP}/${var}_${member}_${dtg}.nc
else 
    out_file=${TOPDIR_OUTPUT}/${EXP}/${var}_${dtg}.nc
fi

area_file=$(dirname ${out_file})/cice_area.nc
if [[ ! -f ${area_file} ]]; then
    echo "making area file"
    if [[ ${MODEL} == GEFS ]]; then
        f=$(ls ${src_dir}/iceh*${member}.nc | tail -1)
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


############
#   IC file
file_tau_list=""
if [[ ${MODEL} == 'GFS' ]]; then
    # GEFS IC is also written out
    in_file=$(ls ${src_dir}/iceic*nc)
    if [[ -z ${in_file} ]]; then
        echo "ic file not found in:" ${src_dir}
        exit 1
    fi
    tau=000
    out_tau_file=${TOPDIR_OUTPUT}/TEMP/${dtg}/CICE_${dtg}_M${member}_${tau}.nc
    CICE_PARSE ${in_file} ${out_tau_file} ${var}
    (( $? != 0 )) && exit 1
    file_tau_list=${file_tau_list}' '${out_tau_file}
fi
############
# tau files
if [[ ${MODEL} == 'GEFS' ]]; then
    files=$(ls ${src_dir}/iceh*${member}.nc)
else
    files=$(ls ${src_dir}/ice[1,2]*.nc)
fi

for f in ${files}; do
    if [[ ${MODEL} == 'GEFS' ]]; then
        f_name=$(basename ${f}) 
        f_dtg=${f_name:5:4}${f_name:10:2}${f_name:13:2}00
    else
        f_dtg=$(basename ${f}) && f_dtg=${f_dtg:3:10}
    fi
    tau=$( ${SCRIPT_DIR}/CALC_tau.sh ${dtg} ${f_dtg}) && tau=$(printf "%03d" $tau)
    out_tau_file=${TOPDIR_OUTPUT}/${EXP}/TEMP/${dtg}/CICE_${dtg}_M${member}_${tau}.nc
    CICE_PARSE ${f} ${out_tau_file} ${var}
    (( $? != 0 )) && exit 1
    file_tau_list=${file_tau_list}' '${out_tau_file}
done

ncecat -u tau ${file_tau_list} ${out_file}
(( $? != 0 )) && exit 1
ncap2 -s 'time(:)={"2018-01-24T00:00:00.000000000"}' aice_d_2018012400.nc out.nc
exit 1

rm ${file_tau_list}
rm -r ${TOPDIR_OUTPUT}/${EXP}/TEMP/${dtg}/CICE_${dtg}_M${member}_???.nc
echo "CREATED:" ${out_file}
echo " "

