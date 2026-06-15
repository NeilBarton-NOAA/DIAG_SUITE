#!/bin/sh
set -u
exp=retrov17_01_realtime
dir_hpss="/5year/NCEPDEV/emc-global/emc.glopara/WCOSS2/GFSv17/${exp}/*00/"
file_hpss=ice_6hravg.tar
num_files=64 && file_name="6hr_avg*nc"
BACKGROUND_JOB=F
source ${PWD}/machine/config.sh && machine_config ${PWD}
export exp_dir=${COMROOT}/${exp}
mkdir -p ${exp_dir}

########################
# get all tar files that are available 
main(){
hpss_find_log=${PWD}/logs/${exp}.$(basename ${file_hpss}).log
if [[ ! -f ${hpss_find_log} ]]; then
    echo "Finding files on HPSS"
    echo " hsi -q find ${dir_hpss}/ -name ${file_hpss} 2>&1 | grep NCEP "
     hsi -q find ${dir_hpss}/ -name ${file_hpss} 2>&1 | grep NCEP > ${hpss_find_log}
fi
files=$(cat ${hpss_find_log})

for f in ${files}; do
    echo $f
    dtg=$( echo "${f}" | awk -F'/' '{print $(NF-1)}' )
    echo "  downloading ${f}"
    JOB_NAME=GET.${exp}.$(basename ${f%.tar}).${dtg}
    machine_config ${PWD}
    correct_n_files "${exp_dir}/*.${dtg:0:8}/${dtg:8:2}" "${file_name}" ${num_files}
    if [[ ${FILES_CORRECT} != T ]]; then
        if [[ ${BACKGROUND_JOB} == T ]]; then
            set -x
            cd ${exp_dir} && htar -xvf ${f}
            set +x
        else
            ${SUBMIT_HPSS} --wrap="cd ${exp_dir} && htar -xvf ${f}"
        [[ ${?} > 0 ]] && echo "FATAL with SUBMIT_HPSS" && exit 1
        fi
        exit 1
    fi
done
}

################################################
# options for experiments
exp_options(){
case ${exp} in 
    'RETROV17')    
        dir_hpss='/5year/NCEPDEV/emc-global/emc.glopara/*/GFSv17/retrov17*stream1a/*00'
        file_hpss=${file_hpss:-'ice_6hravg.tar'}
        ;;
    * ) 
        echo 'FATAL: case unknowned ' && exit 1
esac
}

################################################
# check the number of files downloaded as there code have been an issue
correct_n_files () {
dir=${1}
file_search=${2}
expected_files=${3:-1e10}
nfiles=$( find ${dir}/ -name *${file_search}* 2>/dev/null | wc -l )
FILES_CORRECT=F
if (( ${nfiles} == ${expected_files} )); then
    files=$( find ${dir} -name ${file_search} )
    SIZES=$( ls ${files} | awk '{print $5}' | sort -u | wc -l )
    (( ${SIZES} == 1 )) && FILES_CORRECT=T
fi
}

main

############################################################

