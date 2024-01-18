#!/bin/bash
set -u
#CRDATE to seconds

DTG_1=$1
DTG_2=$2

YEAR=${DTG_1:0:4}
MONTH=${DTG_1:4:2}
DAY=${DTG_1:6:2}
HOUR=${DTG_1:8:2}
HOUR_1=$(date -u -d"${YEAR}-${MONTH}-${DAY} ${HOUR}:00:00" +%s)
HOUR_1=$(( HOUR_1 / 3600 ))

YEAR=${DTG_2:0:4}
MONTH=${DTG_2:4:2}
DAY=${DTG_2:6:2}
HOUR=${DTG_2:8:2}
HOUR_2=$(date -u -d"${YEAR}-${MONTH}-${DAY} ${HOUR}:00:00" +%s)
HOUR_2=$(( HOUR_2 / 3600 ))

TAU=$((HOUR_2 - HOUR_1))

echo $TAU
exit 0
