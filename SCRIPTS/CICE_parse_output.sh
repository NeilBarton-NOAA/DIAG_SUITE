#!/bin/sh
set -ux
dtg=${1}
var=${2}
EXP=${3}
ENS_MEMBERS=${4}
member=$(printf "%02d" ${4})

SCRIPT_DIR=$(dirname "$0")
source ${SCRIPT_DIR}/experiment_options.sh ${EXP} ${dtg}
source ${SCRIPT_DIR}/functions.sh ${EXP}

src_dir=${local_ice_dir}

if (( ${ENS_MEMBERS} > 0 )); then
    out_file=${TOPDIR_OUTPUT}/${EXP}/${var}_${member}_${dtg}.nc
else 
    out_file=${TOPDIR_OUTPUT}/${EXP}/${var}_${dtg}.nc
fi

area_file=$(dirname ${out_file})/cice_area.nc
if [[ ! -f ${area_file} ]]; then
    echo "making area file"
    f=$(ls ${src_dir}/*ice*.nc | tail -1)
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
# GEFS IC is also written out
in_file=$(ls ${src_dir}/iceic*nc 2>/dev/null)
if [[ ! -f ${in_file} ]]; then
    in_file=$(ls ${src_dir}/*.ic.nc)
fi
tau=000
out_tau_file=${TOPDIR_OUTPUT}/${EXP}/TEMP/${dtg}/CICE_${dtg}_M${member}_${tau}.nc
CICE_PARSE ${in_file} ${out_tau_file} ${var} ${ENS_MEMBERS}
(( $? != 0 )) && exit 1
file_tau_list=${file_tau_list}' '${out_tau_file}

############
# tau files
files=$( ls ${src_dir}/${file_search} )
for f in ${files}; do
    echo ${f}
    if [[ ${file_search:0:4} == 'iceh' ]]; then
        f_name=$(basename ${f}) 
        f_dtg=${f_name:5:4}${f_name:10:2}${f_name:13:2}00
        tau=$( ${SCRIPT_DIR}/CALC_tau.sh ${dtg} ${f_dtg}) && tau=$(printf "%03d" $tau)
    elif [[ ${file_search:0:9} == 'gfs.ice.t' ]]; then
        f_name=$(basename ${f}) && tau=${f_name:22:3}
    elif [[  ${file_search:0:4} == 'ice[' ]]; then
        f_dtg=$(basename ${f}) && f_dtg=${f_dtg:3:10}
        tau=$( ${SCRIPT_DIR}/CALC_tau.sh ${dtg} ${f_dtg}) && tau=$(printf "%03d" $tau)
    else
        'unknown how to get tau from file'
        exit 1
    fi
    out_tau_file=${TOPDIR_OUTPUT}/${EXP}/TEMP/${dtg}/CICE_${dtg}_M${member}_${tau}.nc
    CICE_PARSE ${f} ${out_tau_file} ${var} ${ENS_MEMBERS}
    (( $? != 0 )) && exit 1
    file_tau_list=${file_tau_list}' '${out_tau_file}
done

ncecat -u tau ${file_tau_list} ${out_file}
(( $? != 0 )) && exit 1

rm ${file_tau_list}
rm -r ${TOPDIR_OUTPUT}/${EXP}/TEMP/${dtg}/CICE_${dtg}_M${member}_???.nc
echo "CREATED:" ${out_file}
echo " "
