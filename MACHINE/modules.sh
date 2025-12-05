#!/bin/sh
machine=$(uname -n)
if [[ ${machine:0:3} == hfe || ${machine} == h*[cm]* ]]; then
    machine=hera
    export WORK_DIR=/scratch2/NCEPDEV/stmp3
elif [[ ${machine} == hercules* ]]; then
    machine=hercules
    export WORK_DIR=/work/noaa/marine
elif [[ ${machine} == gaea* || ${machine} == dtn* || ${machine} == c6* ]]; then
    machine=gaea
    export WORK_DIR=/gpfs/f6/sfs-emc/scratch
elif [[ ${machine} == u* ]]; then
    machine=ursa
    export WORK_DIR=/scratch4/NCEPDEV/stmp
else
    echo 'FATAL: MACHINE UNKNOWN'
    exit 1
fi

echo "${SCRIPT_DIR}/MACHINE/modules_${machine}.sh"
source ${SCRIPT_DIR}/MACHINE/modules_${machine}.sh
