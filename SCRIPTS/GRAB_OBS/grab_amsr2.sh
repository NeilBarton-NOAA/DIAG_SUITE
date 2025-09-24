#!/bin/sh
########################
# wget data from nsidc
# sign-in information at ~/.netrc
# https://n5eil01u.ecs.nsidc.org/DP1/AMSA/AU_SI25.001/2024.01.01/AMSR_U2_L3_SeaIce25km_B04_20240101.he5
set -u
DTG=${1:0:8} 
DES=${2}/ice_concentration/amsr2
SITE=https://n5eil01u.ecs.nsidc.org/DP1/AMSA/AU_SI25.001

########################
########################
WGET () {
DTG=${1}
DES_DIR=${2}
YEAR=${DTG:0:4}
MONTH=${DTG:4:2}
DAY=${DTG:6:2}
SRC_DIR=https://n5eil01u.ecs.nsidc.org/DP1/AMSA/AU_SI25.001/${YEAR}.${MONTH}.${DAY}
f=AMSR_U2_L3_SeaIce25km_B04_${DTG}.he5
if [[ ! -f ${DES_DIR}/${f} ]]; then
    wget --load-cookies ~/.urs_cookies --save-cookies ~/.urs_cookies \
        --keep-session-cookies --auth-no-challenge=on \
        -P  ${DES_DIR} \
        ${SRC_DIR}/${f}
else
    echo "file already downloaded", ${DES_DIR}/${f}
fi
}

########################
########################
mkdir -p ${DES} && cd ${DES}
END_DTG=$(date -d "${DTG} + 48 day" +%Y%m%d)
while [ "${DTG}" != ${END_DTG} ]; do
    echo ${DTG}
    WGET ${DTG} ${DES_DIR}
    START_DTG=$(date -d "${DTG} + 1 day" +%Y%m%d)
done

