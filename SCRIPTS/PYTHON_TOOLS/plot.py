import calendar
import numpy as np
import matplotlib.pyplot as plt

def ice_extent_per_month(DATS, OBS = None):
    # one plot per month for data of sea ice extent
    # doesn't assume number of DATS
    if OBS != None:
        if type(OBS) != list:
            OBS = [OBS]
    ALL_DS = DATS.copy()
    if len(OBS) > 0:
        for OB in OBS:
            ALL_DS.append(OB) 
    for pole in ['north', 'south']:
        for month in np.arange(1,13):
            for i, ds in enumerate(ALL_DS):
                c_time = ds['time'].isel(time = ds['time'].dt.month.isin([month]))
                if i == 0:
                    a_time = c_time
                else:
                    same_times = np.array(list(set(c_time.values) & set(a_time.values)))
            if len(same_times) > 0:
                # plot model data with tau
                name = calendar.month_abbr[month].upper() + '_' + pole + 'extent_'
                for i, ds in enumerate(DATS):
                    dat = ds['extent'].sel(time = same_times, hemisphere = pole).mean('time')
                    try:
                        text = ds.test_name
                    except:
                        text = str(i)
                    if 'member' in dat.dims:
                        plt.plot(dat['tau'].values, dat.mean('member').values, linewidth = 2.0, label = text )
                        plt.fill_between(dat['tau'].values, dat.min('member').values, dat.max('member').values, alpha = 0.5)
                    else:
                        dat.plot(linewidth = 2.0, label = text)
                    name = name + text.replace(':', '').replace(' ','').replace('/','') + '_'
                # observations
                #   get times for obs
                last_tau = int(ds['tau'][-1].values)
                styles = ['-','--']
                for j, obs in enumerate(OBS):
                    ob = []
                    for t in same_times:
                        t_last = t + np.timedelta64(last_tau, 'D')
                        ob.append(obs['extent'].sel(time = slice(t, t_last), hemisphere = pole).values)
                    ob = np.mean(np.array(ob), axis = 0)
                    try:
                        text = obs.test_name
                    except:
                        text = 'Obs'
                    plt.plot(np.arange(0, ob.size, 1), ob, color = 'k', linestyle = styles[j], linewidth = 2.0, label = text)
                name = name + text.replace(':', '').replace(' ','').replace('/','') 
                name = name.replace(pole,'')
                try:
                    save_dir = DATS[0].save_dir
                except:
                    save_dir = './'
                fig_name = save_dir + '/' + pole[0].upper() + 'H_' + name + '.png'
                plt.legend(frameon = False)
                plt.xlabel('Forecast Day')
                plt.ylabel(pole[0].upper() + 'H Sea Ice Extent')
                plt.title(pole[0].upper() + 'H Sea Ice Extent: ' + calendar.month_abbr[month])
                #plt.show()
                plt.savefig(fig_name, bbox_inches = 'tight')
                print('SAVED:', fig_name)
                plt.close()
                #exit(1)

def ice_extent_imshowdiff(DAT1, DAT2, pole = 'north'):
    dat_plot = []
    y_label = []
    try:
        taus = DAT1['tau'].values
    except:
        taus = DAT2['tau'].values
    for m in np.arange(12) + 1:
    #for m in [8]: #np.arange(1,13):
        dat = []
        y_label.append(calendar.month_abbr[m])
        d1_time = DAT1['time'].isel(time = DAT1['time'].dt.month.isin([m]))
        d2_time = DAT2['time'].isel(time = DAT2['time'].dt.month.isin([m]))
        same_times = np.array(list(set(d1_time.values) & set(d2_time.values)))
        if len(same_times) > 0:
            for ds in [DAT1, DAT2]:
                if 'tau' not in ds.keys():
                    # Observations
                    last_tau = int(DAT1['tau'][-1].values)
                    ob = []
                    for t in same_times:
                        t_last = t + np.timedelta64(last_tau, 'D')
                        obs = ds['extent'].sel(time = slice(t, t_last), hemisphere = pole).values
                        ob.append(np.interp(taus, np.arange(0, obs.size), obs))
                    d = np.mean(np.array(ob), axis = 0)
                else:
                    if 'member' in ds.dims:
                        d = ds['extent'].sel(time = same_times, hemisphere = pole).mean(['time','member'])
                    else:
                        d = ds['extent'].sel(time = same_times, hemisphere = pole).mean('time')
                d = np.ma.masked_where(d == 0, d)
                dat.append(d)
            diff = dat[0] - dat[1]
            if (diff.size > np.max(taus)): # if taus aren't integers of days
                diff = np.interp(np.arange(np.min(taus), np.max(taus) + 1), taus, diff)
        else:
            diff = np.empty(diff.size)
        dat_plot.append(diff)
    dat_plot = np.array(dat_plot)
    try:
        title = pole[0].upper() + 'H: ' + DAT1.test_name + ' minus ' + DAT2.test_name
    except:
        title = pole[0].upper() + 'H: DAT1 minus DAT2'
    print(title)
    print(' Min:', np.round(np.nanmin(dat_plot),2), '  Max:', np.round(np.nanmax(dat_plot),2))
    try:
        vmin = DAT1.DMIN
        vmax = DAT1.DMAX
    except:
        mi = np.nanmin(dat_plot)
        ma = np.nanmax(dat_plot)
        if abs(mi) > abs(ma):
            vmin = mi
            vmax = -1 * vmin
        else:
            vmax = ma
            vmin = -1 * vmax
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(1,1,1)
    cmap = plt.get_cmap('seismic')
    im = ax.imshow(dat_plot, cmap = cmap, 
                    vmin = vmin, vmax = vmax, 
                    aspect = 'auto', 
                    interpolation = 'none')
    cbar = plt.colorbar(im)
    cbar.set_label('million sq km') 
    taus = np.arange(np.min(taus), np.max(taus) + 1)
    plt.xticks(np.arange(taus.size)[::3], taus[::3].astype('int'))
    plt.yticks(np.arange(12), y_label)
    ax.set_xlabel('Forecast Day')
    ax.set_title(title, fontsize = 16, fontweight = 'bold')
    #plt.show()
    try:
        save_dir = DAT1.save_dir
    except:
        save_dir = './'
    fig_name = save_dir + '/' + pole[0].upper() + 'H_extent_MONTHvsTAU_' + title[2::].replace(' ','').replace(':','').replace('/','') + '.png'
    plt.savefig(fig_name, bbox_inches = 'tight')
    plt.close()
    print('SAVED:', fig_name)

