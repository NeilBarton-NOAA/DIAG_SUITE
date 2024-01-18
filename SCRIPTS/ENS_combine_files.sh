#!/bin/sh
set -xu
dtg=${1}
var=${2}
topdir=${3} 

out_file=${topdir}/${var}_${dtg}.nc

if [[ -f ${out_file} ]]; then
    echo "${out_file} already made"
    echo ""
    exit 0
fi

files=$( ls ${topdir}/${var}_*_${dtg}.nc )
ncecat -u member ${files} ${out_file}
(( $? != 0 )) && exit 1
rm ${files}

#mean
#ncra ${files} ${out_file}

echo "CREATED:" ${out_file}
echo " "

