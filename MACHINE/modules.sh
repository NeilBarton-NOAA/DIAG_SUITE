#!/bin/sh
machine=$(uname -n)
if [[ ${machine:0:3} == hfe || ${machine} == h*[cm]* ]]; then
    machine=hera
elif [[ ${machine} == hercules* ]]; then
    machine=hercules
elif [[ ${machine} == gaea* || ${machine} == dtn* || ${machine} == c6* ]]; then
    machine=gaea
else
    echo 'FATAL: MACHINE UNKNOWN'
    exit 1
fi

echo "${SCRIPT_DIR}/MACHINE/modules_${machine}.sh"
source ${SCRIPT_DIR}/MACHINE/modules_${machine}.sh
