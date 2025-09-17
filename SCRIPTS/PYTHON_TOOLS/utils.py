# new utils
def debug(exit_program = False):
    import os
    debug = os.environ.get('DEBUG_DIAG', False)
    if (debug == True) and (exit_program == True):
        print("Debug Flag is on, will exit")
        exit(1)
    else:
        return debug


