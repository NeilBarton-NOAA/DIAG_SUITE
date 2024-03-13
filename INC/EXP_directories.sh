#!/bin/sh
set -xu

# Location of DATA, if on hera, scripts will not download data
case ${EXP} in 
    'HR1' )     DIR_DATA="/NCEPDEV/emc-climate/5year/Jiande.Wang/WCOSS2/HR1";;
    'HR2' )     DIR_DATA="/NCEPDEV/emc-climate/5year/role.ufscpara/{WCOSS2,HERA}/HR2";;
    'EP4' )     DIR_DATA='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep4/ep4_f';;
    'EP4a' )    DIR_DATA='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep4a';;
    'EP5')      DIR_DATA='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep5' ;;
    'EP5r1')    DIR_DATA='/NCEPDEV/emc-ensemble/2year/Bing.Fu/ep5r1' ;;
    'DA_TEST' )      DIR_DATA='/scratch1/NCEPDEV/stmp2/Lydia.B.Stefanova/DA';;

* ) echo 'FATAL: case unknowned ' && exit 1
esac


