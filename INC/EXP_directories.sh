#!/bin/sh
set -xu

case ${EXP} in 
    'HR1' ) DIR_HPSS="/NCEPDEV/emc-climate/5year/Jiande.Wang/WCOSS2/HR1";;
    'HR2' ) DIR_HPSS="/NCEPDEV/emc-climate/5year/role.ufscpara/{WCOSS2,HERA}/HR2";;
    'EP4' ) DIR_HPSS='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep4/ep4_f';;
    'EP4a' ) DIR_HPSS='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep4a';;
    'GDAS' ) DIR_HPSS='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep4a';;
    * ) echo 'FATAL: case unknowned ' && exit 1
esac
