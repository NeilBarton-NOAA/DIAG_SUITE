# DIAG_SUITE
diagnostic tools for ufs/gefs/gfs/sfs

DEPENDENCIES:
    cylc, python3 (matplotlib, xesmf, xarray, others), nco

USE of CYCL:
    if this is the first time using cylc, you'll likely need to add a
    ~/.cylc/flow/global.cylc
    examine and copy ~Neil.Barton/.cylc/flow/global.cylc
    and define ${CYLC_WORKDIR} to a space in your account

MODULES FOR DEPENDENCIES on hera:
    Must load on command line!
        module use -a ~Neil.Barton/TOOLS/modulefiles
        module cylc
    Other modules loaded in Scripts

TO RUN:
    open suite.rc and edit top parameters if needed
        e.g.: MODEL, MAIL_ADDRESS, EXPS
    validate suite
        cylc va $PWD (Directory of flow.cylc file)
    register suite, validate, and run suite
        cylc vip -n $NAME $PWD/flow.cylc
        ($NAME is arbitrary, $PWD is the directory of the flow.cycl file)
    check to see what is running
        cylc tui $NAME 

TO ADD MORE EXPERIMENTS:
    open SCRIPTS/experiment_options.sh
        and add the options/variables similar to the HR3a  
    double check the DATES variable in the suite.rc file

OTHER USEFUL CYLC COMMANDS:
