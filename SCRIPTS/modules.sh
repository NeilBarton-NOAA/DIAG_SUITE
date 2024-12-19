#!/bin/sh
machine=$(uname -n)
if [[ ${machine:0:3} == hfe ]]; then
    machine=hera
elif [[ ${machine} == hercules* ]]; then
    machine=hercules
else
    echo 'FATAL: MACHINE UNKNOWN'
    exit 1
fi

source ${SCRIPT_DIR}/modules_${machine}.sh
