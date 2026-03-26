#!/bin/sh
set -u
EXP=${1:-'RETROV17'}
MODEL=${2:-'ice'}
BACKGROUND_JOB=F
DIAG_DIR=${PWD}
source ${DIAG_DIR}/MACHINE/config.sh 
EXPDIR=${TOPDIR_OUTPUT}/${EXP} && mkdir -p ${EXPDIR} && cd ${EXPDIR}
########################
# options for experiments
case ${EXP} in 
    'RETROV17')    
        HPSS_DIR='/5year/NCEPDEV/emc-global/emc.glopara/*/GFSv17/retrov17*'
        RUN='gfs'
        ice_hpss_file='ice_6hravg.tar'
        ocn_hpss_file='ocean_6hravg.tar'
        ;;
* ) echo 'FATAL: case unknowned ' && exit 1
esac
[[ ${MODEL} == 'ice' ]] && HPSS_FILE=${ice_hpss_file}
[[ ${MODEL} == 'ocn' ]] && HPSS_FILE=${ocn_hpss_file}

########################
# check the number of files downloaded as there code have been an issue
correct_n_files () {
dir=${1}
# no check for ensembles at this point
CORRECT=F
nfiles=$(ls ${dir}/*nc 2>/dev/null | grep -v '.ic.nc' 2>/dev/null | wc -l )
if (( ${nfiles} > 0 )); then
    SIZES=$( ls -l ${dir}/*nc | grep -v '.ic.nc' | awk '{print $5}' | sort -u | wc -l )
    (( ${SIZES} == 1 )) && CORRECT=T
fi
echo ${CORRECT}
}

########################
# get all tar files that are available 
files=$( hsi -q find ${HPSS_DIR}/*00 -name ${HPSS_FILE} 2>&1 | grep NCEPDEV )
i=0
for f in ${files}; do
    dtg=$( echo "${f}" | awk -F'/' '{print $(NF-1)}' )
    local_dir=${TOPDIR_OUTPUT}/${EXP}/${RUN}.${dtg:0:8}/${dtg:8:10}/model/${MODEL}/history   
    FILES_PRESENT=$( correct_n_files "${local_dir}")
    f_out=${TOPDIR_OUTPUT}/${EXP}/${MODEL}_${dtg}.nc
    if [[ ${FILES_PRESENT} == F && ! -f ${f_out} ]]; then
        echo "  downloading ${f}"
        JOB_NAME=GET.${EXP}.$(basename ${f%.tar}).${dtg}
        source ${DIAG_DIR}/MACHINE/config.sh
        ${SUBMIT_HPSS} htar -xvf ${f}
        [[ ${?} > 0 ]] && echo "FATAL with SUBMIT_HPSS" && exit 1
        #i=$(( i + 1 ))
        #(( i > 5 )) && exit 1
    fi
done
