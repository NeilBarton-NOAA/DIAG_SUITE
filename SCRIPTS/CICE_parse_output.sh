#!/bin/sh
set -xu
dtg=${1}
var=${2}
indir=${3}
outdir=${4} 
member=$(printf "%02d" ${5})

mkdir -p ${outdir}

############
# check in dir
if [[ ! -d ${indir} ]]; then
    indir=${outdir}
fi

EXP=${outdir##*/}
if [[ ${MODEL} == 'GEFS' ]]; then
    if [[ ${EXP} == 'EP5r1' ]]; then
        dir=$( ls -d ${indir}/$(( ${dtg:0:8} + 1 ))/ice/ )
    else
        dir=$( ls -d ${indir}/${dtg:0:8}/ice/ )
    fi
elif [[ ${EXP} == HR1 ]]; then
    dir=$( ls -d ${indir}/*.${dtg:0:8}/${dtg:8:2}/ice/ )
else
    dir=$( ls -d ${indir}/*.${dtg:0:8}/${dtg:8:2}/model_data/ice/history )
fi

if [[ ${MODEL} == 'GEFS' ]]; then
    out_file=${outdir}/${var}_${member}_${dtg}.nc
else 
    out_file=${outdir}/${var}_${dtg}.nc
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
mkdir -p $( dirname ${out_tau_file} )
if [[ ${MODEL} == 'GEFS' ]]; then
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

############
#   IC file
file_tau_list=""
if [[ ${MODEL} == 'GFS' ]]; then
    # GEFS IC is also written out
    in_file=$(ls ${dir}/iceic*nc)
    if [[ -z ${in_file} ]]; then
        echo "ic file not found in:" ${dir}
        exit 1
    fi
    tau=000
    out_tau_file=${outdir}/TEMP/${dtg}/CICE_${dtg}_M${member}_${tau}.nc
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
    out_tau_file=${outdir}/TEMP/${dtg}/CICE_${dtg}_M${member}_${tau}.nc
    CICE_PARSE ${f} ${out_tau_file} ${var}
    (( $? != 0 )) && exit 1
    file_tau_list=${file_tau_list}' '${out_tau_file}
done

ncecat -u tau ${file_tau_list} ${out_file}
(( $? != 0 )) && exit 1
rm ${file_tau_list}
rm -r ${outdir}/TEMP/${dtg}/CICE_${dtg}_M${member}_???.nc
echo "CREATED:" ${out_file}
echo " "

