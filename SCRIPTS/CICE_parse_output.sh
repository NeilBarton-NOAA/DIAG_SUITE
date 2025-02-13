#!/bin/sh
set -eux
dtg=${1}
var=${2}
EXP=${3}
MEM=$(printf "%03d" ${4})
ENS_MEMBERS=${5}

SCRIPT_DIR=$(dirname "$0")
source ${SCRIPT_DIR}/experiment_options.sh ${EXP} ${dtg}
source ${SCRIPT_DIR}/functions.sh ${EXP}
source ${SCRIPT_DIR}/workflow_options.sh

src_dir=${local_ice_dir}
[[ ${WORKFLOW} == GEFS ]] && MEM=${MEM:1:2}
[[ ${WORKFLOW} == GW ]] && src_dir=${local_download_dir}/${RUN}.${dtg:0:8}/${dtg:8:10}/mem${MEM}/model/ice/history   

############
# Make area file
area_file=${TOPDIR_OUTPUT}/${EXP}/cice_area.nc
if [[ ! -f ${area_file} ]]; then
    echo "making area file"
    f=$(ls ${src_dir}/*ice*.nc | tail -1)
    ncks -v tarea ${f} ${area_file}
    (( $? != 0 )) && exit 1
fi
# Check if File already exist
if (( ${ENS_MEMBERS} > 0 )); then
    out_file=${TOPDIR_OUTPUT}/${EXP}/TEMP/${var}_${MEM}_${dtg}.nc
else 
    out_file=${TOPDIR_OUTPUT}/${EXP}/${var}_${dtg}.nc
fi
if [[ -f ${out_file} ]]; then
    echo "${out_file} already made"
    echo ""
    exit 0
fi

# Find tau
i=1
if [[ ${WORKFLOW} == 'GEFS' ]]; then
    files=$( ls ${src_dir}/*${MEM}.nc | head -n 3)
    nfiles=$( ls ${src_dir}/*${MEM}.nc 2>/dev/null | wc -l )
    for f in ${files}; do 
        dp=${f##*ice?.}
        [[ ${i} == 2 ]] && date2=$( date -d "${dp:0:10}" +%s) && TAU=$(( (date2 - date) / 3600 )) 
        [[ ${i} == 3 ]] && date2=$( date -d "${dp:0:10}" +%s) && TAU2=$(( (date2 - date) / 3600 )) 
        date=$( date -d "${dp:0:10}" +%s)
        i=$(( i + 1 ))
    done
elif [[ ${WORKFLOW} == "GW" ]]; then
    files=$( ls ${src_dir}/*.nc | head -n 2)
    nfiles=$( ls ${src_dir}/*.nc 2>/dev/null | wc -l )
    for f in ${files}; do 
        [[ ${i} == 1 ]] && TAU=${f##*.f} && TAU=${TAU%%.nc*} && TAU=${TAU#0}
        [[ ${i} == 2 ]] && TAU2=${f##*.f} && TAU2=${TAU2%%.nc*} && TAU2=$(( 10#$TAU2 - 10#$TAU ))
        i=$(( i + 1 ))
    done
fi

if (( TAU != TAU2 )); then
    echo "FATAL: TAUS do not match for files" ${TAU} ${TAU2}
    for f in ${files}; do
        echo ${f}
    done
    exit 1
fi
cice_var=$(cice_var_name ${f} ${var})

file_tau_list=""
MAX_TAU=$(( nfiles * TAU ))
for tau in $( seq 24 ${TAU} ${MAX_TAU}); do
    if [[ ${WORKFLOW} == 'GEFS' ]]; then
        f_tau=$(( tau - TAU ))
        f_dtg=$(date -u -d"${dtg:0:4}-${dtg:4:2}-${dtg:6:2} 00:00:00 ${f_tau} hours" +%Y-%m-%d)
        f=$( ls ${src_dir}/ice?.${f_dtg}.?${MEM}.nc )
    elif [[ ${WORKFLOW} == "GW" ]]; then
        f_tau=$(printf "%03d" ${tau})
        f=$(ls ${src_dir}/*ice*.f${f_tau}.nc )
    fi
    out_tau_file=${TOPDIR_OUTPUT}/${EXP}/TEMP/${dtg}/CICE_${dtg}_${var}_M${MEM}_${f_tau}.nc
    echo ${f_tau} ${f}    
    CICE_PARSE ${f} ${out_tau_file} ${cice_var} ${ENS_MEMBERS}
    file_tau_list=${file_tau_list}' '${out_tau_file}
done

ncecat -u tau ${file_tau_list} ${out_file}
(( $? != 0 )) && exit 1

rm ${file_tau_list}
echo "CREATED:" ${out_file}
echo " "

exit 0
