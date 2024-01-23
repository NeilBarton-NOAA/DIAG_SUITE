#!/bin/sh
set -xu

# Location on HPSS
case ${EXP} in 
    'HR1' ) DIR_HPSS="/NCEPDEV/emc-climate/5year/Jiande.Wang/WCOSS2/HR1";;
    'HR2' ) DIR_HPSS="/NCEPDEV/emc-climate/5year/role.ufscpara/{WCOSS2,HERA}/HR2";;
    'EP4' ) DIR_HPSS='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep4/ep4_f';;
    'EP4a' ) DIR_HPSS='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep4a';;
    'CICETEST' ) DIR_HPSS='LOCAL_ONLY';;

* ) echo 'FATAL: case unknowned ' && exit 1
esac

# Location on hera 
case ${EXP} in 
    'CICETEST' ) export DIR_HERA='/scratch1/NCEPDEV/stmp2/Lydia.B.Stefanova/DA';;
    * ) echo 'FATAL: case unknowned ' && exit 1
esac

