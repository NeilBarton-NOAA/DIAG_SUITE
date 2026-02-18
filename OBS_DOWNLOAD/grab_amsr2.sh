#!/bin/sh
########################
# wget data from nsidc
# sign-in information at ~/.netrc
# https://n5eil01u.ecs.nsidc.org/DP1/AMSA/AU_SI25.001/2024.01.01/AMSR_U2_L3_SeaIce25km_B04_20240101.he5
set -u
DTG=${1}
END_DTG=$(date -d "${2} + 48 day" +%Y%m%d)
TARGET_SEC=$(date -d "${END_DTG}" +%s)
CURRENT_SEC=$(date +%s)
if [[ ${TARGET_SEC} -gt ${CURRENT_SEC} ]]; then
    END_DTG=$(date -d "5 days ago" +%Y%m%d)
fi

DES=${TOPDIR_OBS}/ice_concentration/amsr2
SITE=https://n5eil01u.ecs.nsidc.org/DP1/AMSA/AU_SI25.001

########################
########################
WGET () {
DTG=${1}
DES=${2}
YEAR=${DTG:0:4}
MONTH=${DTG:4:2}
DAY=${DTG:6:2}
SRC_DIR=https://n5eil01u.ecs.nsidc.org/DP1/AMSA/AU_SI25.001/${YEAR}.${MONTH}.${DAY}
f=AMSR_U2_L3_SeaIce25km_B04_${DTG}.he5
if [[ ! -f ${DES}/${f} ]]; then
    wget --load-cookies ~/.urs_cookies --save-cookies ~/.urs_cookies \
        --keep-session-cookies --auth-no-challenge=on \
        -P  ${DES} \
        ${SRC_DIR}/${f}
    echo "downloaded", ${f}
else
    echo "file already downloaded", ${f}
fi
}

########################
########################
mkdir -p ${DES} && cd ${DES}
while [ "${DTG}" != ${END_DTG} ]; do
    WGET ${DTG} ${DES}
    DTG=$(date -d "${DTG} + 1 day" +%Y%m%d)
done

