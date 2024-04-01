#!/usr/bin/env sh
set -xu
# take a DTG (YYYYMMDDHH) and add time in days
DTG=${1}
OFFSET=${2:-0}
TIME=${3:-days}

YEAR=${DTG:0:4}
MONTH=${DTG:4:2}
DAY=${DTG:6:2}
HOUR=${DTG:8:2}

OFFSET=$(printf '%d\n' "$OFFSET" 2>/dev/null)

if [[ $OFFSET == *@(-)*  ]]; then
    n=${#OFFSET}
    OFFSET=${OFFSET:1:n-1}
    NEW_DTG=$(date -u -d"${YEAR}-${MONTH}-${DAY} ${HOUR}:00:00 ${OFFSET} ${TIME} ago" +%Y%m%d%H)
elif [[ $OFFSET > 0 ]]; then
    NEW_DTG=$(date -u -d"${YEAR}-${MONTH}-${DAY} ${HOUR}:00:00 ${OFFSET} ${TIME}" +%Y%m%d%H)
else
    NEW_DTG=${DTG}
fi
echo ${NEW_DTG}
exit 0
