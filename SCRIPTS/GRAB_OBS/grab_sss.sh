#!/bin/bash
set -xu
DTG=${1:0:8} 
SCRIPT_DIR=${SCRIPT_DIR:-$(dirname "$0")/../}
source ${SCRIPT_DIR}/experiment_options.sh DUMMY ${DTG}00
DES=${TOPDIR_OBS}/sss/ostia

${SCRIPT_DIR}/GRAB_OBS/cm.py sss ${DTG} ${DES} 48
