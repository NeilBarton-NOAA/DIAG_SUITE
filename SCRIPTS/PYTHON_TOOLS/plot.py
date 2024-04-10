import calendar
import numpy as np
import matplotlib.pyplot as plt

class ice_extent(object):
    pole = 'north'
    save_dir = './'
    @classmethod
    def create(cls):
        # plot model data with tau
        for i, ds in enumerate(cls.dats):
            if cls.times.size == 1:
                dat = ds['extent'].sel(time = cls.times, hemisphere = cls.pole)
            else:
                dat = ds['extent'].sel(time = cls.times, hemisphere = cls.pole).mean('time')
            if 'member' in dat.dims:
                plt.plot(dat['tau'].values, dat.mean('member').values, linewidth = 2.0, label = ds.test_name )
                plt.fill_between(dat['tau'].values, dat.min('member').values, dat.max('member').values, alpha = 0.5)
            else:
                dat.plot(linewidth = 2.0, label = text)
            name = 'ice_extent_' + cls.title.replace(' ','_') + '_' + \
                    ds.test_name.replace(':', '').replace(' ','').replace('/','') + '_'
            # observations; get times for obs
            last_tau = int(ds['tau'][-1].values)
            styles = ['-','--']
            for j, obs in enumerate(cls.obss):
                if cls.times.size == 1:
                    t_last = cls.times + np.timedelta64(last_tau, 'D')
                    ob = obs['extent'].sel(time = slice(cls.times, t_last), hemisphere = cls.pole).values
                else:
                    # loop over times
                    ob = []
                    for t in cls.times:
                        t_last = t + np.timedelta64(last_tau, 'D')
                        ob.append(obs['extent'].sel(time = slice(t, t_last), hemisphere = cls.pole).values)
                    ob = np.mean(np.array(ob), axis = 0)
                try:
                    text = obs.test_name
                except:
                    text = 'Obs'
                plt.plot(np.arange(0, ob.size, 1), ob, color = 'k', linestyle = styles[j], linewidth = 2.0, label = text)
                if j != (len(cls.obss) - 1):
                    name = name + text.replace(':', '').replace(' ','').replace('/','') + '_'
                else:
                    name = name + text.replace(':', '').replace(' ','').replace('/','')
            fig_name = cls.save_dir + '/' + cls.pole[0].upper() + 'H_' + name + '.png'
            plt.legend(frameon = False)
            plt.xlim(int(ds['tau'][0].values), int(ds['tau'][-1].values))
            plt.xlabel('Forecast Day')
            plt.ylabel(cls.pole[0].upper() + 'H Sea Ice Extent')
            plt.title(cls.pole[0].upper() + 'H Sea Ice Extent: ' + cls.title)
            plt.show()
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
        print(same_times)
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

class iiee(object):
    pole = 'north'
    save_dir = './'
    @classmethod
    def create(cls):
        exp_title = ''
        for dat in cls.DATS:
            exp_title = exp_title + dat.test_name + '_'
            for ob in cls.OBS_TYPES:
                print(ob)
                if cls.times.size == 1:
                    data = dat['iiee'].sel(obs_type = ob, pole = cls.pole, time = cls.times)
                else:
                    data = dat['iiee'].sel(obs_type = ob, pole = cls.pole, time = cls.times).mean('time')
                label = dat.test_name + ' vs '
                if 'ice_con' in ob:
                    if 'persistence' in ob:
                        label = label + 'Persistence: ' + ob.split('_')[0].upper() 
                    else:
                        label = label + 'Obs: ' + ob.split('_')[0].upper() 
                else:
                    label = label + ob.capitalize()
                if 'member' in data.dims:
                    plt.plot(data['tau'].values, data.mean('member').values, linewidth = 2.0, label = label )
                    plt.fill_between(data['tau'].values, data.min('member').values, data.max('member').values, alpha = 0.5)
                else:
                    data.plot(linewidth = 2.0, label = label)
        if cls.pole == 'north':
            t = 'Arctic '
        elif cls.pole == 'south':
            t = 'Antarctic '
        plt.title(t + cls.title)
        plt.ylabel('IIEE')
        plt.xlabel('Forecast Day')
        plt.legend(frameon = False)
        fig_name = cls.save_dir + '/' + cls.pole[0].upper() + 'H_iiee_' + exp_title + cls.title.replace(' ','').replace(':','').replace('/','') + '.png'
        plt.savefig(fig_name, bbox_inches = 'tight')
        print('SAVED:', fig_name)  
        #plt.show()
               
#class iiee_min_per_month(object): 
#    e = e.replace(',','').strip()
#        f = tdir + '/' + e + '/iiee.nc'
#        dat = xr.open_dataset(f)
#        dat['tau'] = dat['tau'] / 24.0
#        ob_type_month, y_label = [], []
#        for month in np.arange(1,13):
#            y_label.append(calendar.month_abbr[month])
#            if month < 12:
#                c_time = dat['time'].isel(time = dat['time'].dt.month.isin([month]))
#                title = 'IIEE: ' + calendar.month_abbr[month].upper() + ' ' + e 
#                fig_name = save_dir + '/' + pole[0].upper() + 'H_' + calendar.month_abbr[month].upper() + '_IIEE.png'
#            else:
#                c_time = dat['time']
#                title = 'IIEE: ' + e 
#                fig_name = save_dir + '/' + pole[0].upper() + 'H_ALL_TIMES_IIEE.png'
#            #obs_types = dat['obs_type'].values
#            if (c_time.size > 0):
#                # save data for comparison
#                min_ob_type = []
#                for ob in obs_types:
#                    print(ob)
#                    if 'ice_con' in ob:
#                        label = 'GEFS/EP4'
#                    else:
#                        label = ob.capitalize()
#                    #label = ob.replace('_seaice_conc','')
#                    #label = label.replace('_','-')
#                    data = dat['iiee'].sel(obs_type = ob, pole = pole, time = c_time).mean('time')
#                    if 'member' in data.dims:
#                        plt.plot(data['tau'].values, data.mean('member').values, linewidth = 2.0, label = label )
#                        plt.fill_between(data['tau'].values, data.min('member').values, data.max('member').values, alpha = 0.5)
#                        min_ob_type.append(data.mean('member').values)
#                    else:
#                        data.plot(linewidth = 2.0, label = label)
#                        min_ob_type.append(data.values)
#                    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
#                    #ax = kwargs.pop('ax', plt.gca())
#                    #base_line, = ax.plot(x, y, **kwargs)
#                    #print(base_line.get_color())
#                ob_type_month.append(np.argmin(np.array(min_ob_type), axis = 0))
#                if pole == 'north':
#                    t = 'Arctic '
#                elif pole == 'south':
#                    t = 'Antarctic '
#                plt.title(t + title)
#                plt.ylabel('IIEE')
#                plt.xlabel('Forecast Day')
#                plt.legend(frameon = False)
#                #plt.show()
#                print(fig_name)
  
