#!/bin/bash
set -xu
dtg=${1}
indir=${2}
outdir=${3} 

EXP=${outdir##*/}

mkdir -p ${outdir} && cd ${outdir}

components=CICE
[[ ${components} == CICE ]] && f=ice.tar && dir_name=ice

if [[ ${EXP} == EP4 ]] || [[ ${EXP} == EP4a ]]; then
    nfiles=$(ls ${dtg:0:8}/${dir_name}/*nc 2>/dev/null | wc -l )
else
    nfiles=$(ls gfs.${dtg:0:8}/${DTG:8:2}/${dir_name}/*nc 2>/dev/null | wc -l )
fi

if (( ${nfiles} < 114 )); then
    if [[ ${EXP} == EP4 ]]; then
        dir=$(hsi -q ls ${indir}/${dtg:0:4}/${dtg:0:6}/${dtg:0:8}/gefs.${dtg:0:8}_${dtg:8:10}.${f} 2>&1 | grep :)
        f=gefs.${dtg:0:8}_${dtg:8:10}.${f} 
    elif [[ ${EXP} == EP4a ]]; then
        echo ${indir}
        dir=$(hsi -q ls ${indir}/${dtg:0:4}/${dtg:0:6}/${dtg:0:8}/gefs.${dtg:0:8}_${dtg:8:10}.atmos.${f} 2>&1 | grep :)
        f=gefs.${dtg:0:8}_${dtg:8:10}.atmos.${f} 
        if [[ ${dtg} < 2018010100 ]] || [[ ${dtg} > 2018092500 ]]; then 
            mkdir -p ${dtg:0:8} && cd ${dtg:0:8}
        fi
    else
        dir=$(hsi -q ls ${indir}/*/${dtg}/${f} 2>&1 | grep :)
    fi
    f_get=${dir::-1}/${f}
    htar -xvf ${f_get}
else
    echo "${components} files already downloaded"
fi

