#!/bin/bash
set -u
DTG=${1}
END_DTG=$(date -d "${2} + 48 day" +%Y%m%d)
TARGET_SEC=$(date -d "${END_DTG}" +%s)
CURRENT_SEC=$(date +%s)
if [[ ${TARGET_SEC} -gt ${CURRENT_SEC} ]]; then
    END_DTG=$(date -d "5 days ago" +%Y%m%d)
fi


DES=${TOPDIR_OBS}/sst/ostia

while [[ ${DTG} -le ${END_DTG} ]]; do
    ${DIAG_DIR}/OBS_DOWNLOAD/cm.py sst ${DTG} ${DES} 
    DTG=$(date -d "${DTG} + 1 day" +%Y%m%d)
done

