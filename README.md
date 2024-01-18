# DIAG_SUITE
diagnostic tools for ufs/gefs/gfs/sfs

DEPENDENCIES:
    cylc, python3 (matplotlib, xesmf, xarray, others), nco

MODULES FOR DEPENDENCIES on hera:
    Must load on command line!
        module use -a ~Neil.Barton/TOOLS/modulefiles
        module cylc
    Other modules loaded in Scripts

TO RUN:
    open suite.rc and edit top parameters if needed
        e.g.: MODEL, MAIL_ADDRESS, EXPS
    validate suite
        cylc va suite.rc
    register suite
        cylc reg $NAME (NAME is arbitrary) 
    run suite
        cylc run $NAME
    check to see what is running
        cylc mo $NAME (or cylc mo -r $NAME for only active tasks)

OTHER USEFUL CYLC COMMANDS:
    cylc shutdown -k $NAME (shutdown and kill all tasks associated with the suite)
    cylc reload $NAME (if changes are made in the .rc file, the suite most be validated and reloaded for these changes to take effect)
