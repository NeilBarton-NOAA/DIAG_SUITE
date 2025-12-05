#!/bin/bash
set -u
DTG=${1}
END_DTG=$(date -d "${2} + 48 day" +%Y%m%d)
DES=${TOPDIR_OBS}/sst/ostia

while [[ ${DTG} -le ${END_DTG} ]]; do
    ${DIAG_DIR}/GRAB_OBS/cm.py sst ${DTG} ${DES} 
    DTG=$(date -d "${DTG} + 1 day" +%Y%m%d)
done

