#!/bin/bash
set -xu
DTG=${1}
END_DTG=$(date -d "${2} + 48 day" +%Y%m%d)

DES=${TOPDIR_OBS}/ice_concentration/osi_saf

mkdir -p ${DES} && cd ${DES}
while [[ ${DTG} -le ${END_DTG} ]]; do
    Y=${DTG:0:4}
    M=${DTG:4:2}
    D=${DTG:6:2}
    for hem in nh sh ; do
        f=ice_conc_${hem}_polstere-100_multi_${Y}${M}${D}1200.nc
        if [[ ! -f ${f} ]]; then
            wget ftp://osisaf.met.no/archive/ice/conc/${Y}/${M}/${f}
        else
            echo 'file already downloaded', ${f}
        fi
    done
    DTG=$(date -d "${DTG} + 1 day" +%Y%m%d)
done
