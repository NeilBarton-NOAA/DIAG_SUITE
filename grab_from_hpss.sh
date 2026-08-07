#!/bin/sh
set -u
BACKGROUND_JOB=F

WALLTIME="02:00:00"
source ${PWD}/machine/config.sh && machine_config ${PWD}

# SFS GFS ICs
dir_hpss="/NCEPDEV/emc-marine/5year/Neil.Barton/SFS_GFS_ICS"
file_hpss="2026080100"
export exp_dir="${WORK_DIR}/${USER}/ICs/GFS/C192mx025"
# SFS runs
#exp=beta1.1_CPC_ICs_PND_TOPO
#dir_hpss="/NCEPDEV/emc-marine/5year/Neil.Barton/*/${exp}/*00/"
#file_hpss=product_monthly #namelists
#num_files=64 && file_name="6hr_avg*nc"
#export exp_dir=${COMROOT}/${exp}

# GFS RealTime
#exp=retrov17_01_realtime
#dir_hpss="/5year/NCEPDEV/emc-global/emc.glopara/WCOSS2/GFSv17/${exp}/*00/"
#file_hpss=ice_6hravg
#num_files=64 && file_name="6hr_avg*nc"
#export exp_dir=${COMROOT}/${exp}

mkdir -p ${exp_dir}

########################
# get all tar files that are available 
main(){
hpss_find_log=${PWD}/logs/${exp:-"GET"}.$(basename ${file_hpss}).log
if [[ ! -f ${hpss_find_log} ]]; then
    echo "Finding files on HPSS"
    echo " hsi -q find ${dir_hpss}/ -name "*${file_hpss}*tar" 2>&1 | grep NCEP "
    test=$(hsi ls -l ${dir_hpss} 2>&1)
    [[ ${?} > 0 ]] && echo "FATAL: HPSS error" && exit 1
    hsi -q find ${dir_hpss}/ -name *${file_hpss}*tar 2>&1 | grep NCEP > ${hpss_find_log}
fi
files=$(cat ${hpss_find_log})

for f in ${files}; do
    echo $f
    dtg=$( echo "${f}" | awk -F'/' '{print $(NF-1)}' )
    echo "  downloading ${f}"
    JOB_NAME=GET.${exp:-"F"}.$(basename ${f%.tar}).${dtg}
    machine_config ${PWD}
    correct_n_files "${exp_dir}/*.${dtg:0:8}/${dtg:8:2}" "${file_name:-unknown}" ${num_files:-1e10}
    if [[ ${FILES_CORRECT} != T ]]; then
        if [[ ${BACKGROUND_JOB} == T ]]; then
            set -x
            cd ${exp_dir} && htar -xvf ${f}
            set +x
        else
            if [[ ${BATCH_SYSTEM} == "sbatch" ]]; then
                ${SUBMIT_HPSS} --wrap="cd ${exp_dir} && htar -xvf ${f}"
                [[ ${?} > 0 ]] && echo "FATAL with SUBMIT_HPSS" && exit 1
            elif  [[ ${BATCH_SYSTEM} == "qsub" ]]; then
                echo -e "${SUBMIT_HPSS}\n cd ${exp_dir} && htar -xvf ${f}" > submit.sh
                qsub submit.sh
                rm submit.sh
            fi
        fi
    fi
done
}

################################################
# check the number of files downloaded as there code have been an issue
correct_n_files () {
dir=${1}
file_search=${2}
expected_files=${3}
FILES_CORRECT=F
[[ ${file_search} == "unknown" ]] && return
nfiles=$( find ${dir}/ -name *${file_search}* 2>/dev/null | wc -l )
if (( ${nfiles} == ${expected_files} )); then
    files=$( find ${dir} -name ${file_search} )
    SIZES=$( ls ${files} | awk '{print $5}' | sort -u | wc -l )
    (( ${SIZES} == 1 )) && FILES_CORRECT=T
fi
}

main

############################################################

