################################################
def time_plus_tau(times, tau):
    import numpy as np
    import pandas as pd
    if times.size == 1:
        t_array = (times + pd.to_timedelta(tau, unit = 'h')).to_numpy()
    else:
        times = pd.to_datetime(times)
        t_array = []
        for t in times:
            t_array.append((t + pd.to_timedelta(tau, unit = 'h')).to_numpy())
    return np.array(t_array) 

################################################
def unixtime2dtg(dtg, dtg_text = '%Y-%m-%d %HZ'):
    from time import strftime, gmtime
    return strftime(dtg_text, gmtime(dtg))

################################################
def dtg2unixtime(dtg, string = '%Y%m%d%H'):
    from calendar import timegm
    from time import strptime
    return timegm(strptime(dtg, string))
