#!/bin/sh
set -xu
dtg=${1}
var=${2}
EXP=${3} 

SCRIPT_DIR=$(dirname "$0")
source ${SCRIPT_DIR}/experiment_options.sh ${EXP} ${dtg}

out_file=${TOPDIR_OUTPUT}/${EXP}/${var}_${dtg}.nc

if [[ -f ${out_file} ]]; then
    echo "${out_file} already made"
    echo ""
    exit 0
fi

files=$( ls ${TOPDIR_OUTPUT}/${EXP}/TEMP/${var}_*_${dtg}.nc )
ncecat -u member ${files} ${out_file}
(( $? != 0 )) && exit 1
for f in ${files}; do
    rm ${f}
done

#mean
#ncra ${files} ${out_file}

echo "CREATED:" ${out_file}
echo " "

