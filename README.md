# DIAG_SUITE
evaulation tool for ufs/gefs/gfs/sfs

############
# Main Run Scripts 
experiment_options.sh 
    defines RUN type, HPSS directory of output, and hpss_file (cice, mom6) to grab

GET_OUTPUT_FROM_HPSS.sh ${EXP} ${MODEL:-'ice'}
    script looks for hpss_file defined in experiment_options.sh and downloads these files

GET_OBS.sh ${EXP} ${OBS:-'amsr2 osi_saf ostia sss'}
    grabs observational data type for a time period

INTERP_aice.sh ${EXP}
    interpolates CICE aice variable to a grid
        defaults to 25km grid

CALC_ice.sh ${EXP}
    calculates ice extent and IIEE (intergrated ice edge error) from interpolated cice output

PLOT_ics.sh ${EXP}
    plot ice extent and IIEE compared to observations

DEPENDENCIES:
    python3 (matplotlib, xesmf, xarray, others)


