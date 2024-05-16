#!/bin/sh
set -xu
dtg=${1}
var=${2}
EXP=${3} 

SCRIPT_DIR=$(dirname "$0")
source ${SCRIPT_DIR}/experiment_options.sh ${EXP} ${dtg}
########################
# check if ensemble file is already present and correct size
ENS_CAT=T
out_file=${TOPDIR_OUTPUT}/${EXP}/${var}_${dtg}.nc
if [[ -f ${out_file} ]]; then
    nfiles=$( ls ${TOPDIR_OUTPUT}/${EXP}/${var}*${dtg}.nc 2> /dev/null | wc -l )
    # check size 
    if (( ${nfiles} > 1 )); then
        s_of=$( stat -c %s ${out_file} )
        s_ef=$( stat -c %s ${TOPDIR_OUTPUT}/${EXP}/${var}_01_${dtg}.nc )
        if (( ${s_of} == ${s_ef} )); then
            rm ${out_file} 
        else
            rm ${TOPDIR_OUTPUT}/${EXP}/${var}_??_${dtg}.nc
            ENS_CAT=F
        fi
    else
        ENS_CAT=F
    fi
fi    

if [[ ${ENS_CAT} == T ]]; then
    files=$( ls ${TOPDIR_OUTPUT}/${EXP}/${var}_*_${dtg}.nc )
    ncecat -u member ${files} ${out_file}
    (( $? != 0 )) && exit 1
    rm ${files}
    echo "CREATED:" ${out_file}
    echo " "
else
    echo "${out_file} already made"
    echo ""
fi
echo 'NPB'
echo ${TOPDIR_OUTPUT}/${EXP}
exit 1

#mean
#ncra ${files} ${out_file}

