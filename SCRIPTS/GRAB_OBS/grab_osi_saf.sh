#!/bin/bash
set -u
DTG=${1:0:8} 
DES=${2}/ice_concentration/osi_saf
END_DTG=$(date -d "${DTG} + 48 day" +%Y%m%d)
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
    exit 1
    DTG=$(date -d "${DTG} + 1 day" +%Y%m%d)
done
