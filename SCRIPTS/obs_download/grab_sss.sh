#!/bin/bash
set -xu
DTG=${1}
END_DTG=$(date -d "${2} + 48 day" +%Y%m%d)
DES=${TOPDIR_OBS}/sss

while [[ ${DTG} -le ${END_DTG} ]]; do
    ${DIAG_DIR}/OBS_DOWNLOAD/cm.py sss ${DTG} ${DES} 
    DTG=$(date -d "${DTG} + 1 day" +%Y%m%d)
done
