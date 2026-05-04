    ds = ds.sel(name=['RETROV17', 'analysis'])
    ds.coords['name'] = ds.name.str.replace('RETROV17', 'GFSv17')
    seasons = ['DJF', 'MAM', 'JJA', 'SON']
    names_list = ds.name.values.tolist()
    print(names_list)
    fig, axes = plt.subplots(2, 4, figsize=(20, 10), sharex=True, sharey=True)
    # Flatten axes for easy iteration
    axes = axes.flatten()
    for i, season in enumerate(seasons):
        print(i)
        # Select the specific season and average it
        data_season = ds.sel(pole = 'NH', time=ds.time.dt.season == season).mean(dim='time')
        # Plot on the specific axis
        data_season['extent'].plot(ax=axes[i], x='forecast_day', hue='name', linewidth = 3, marker='o')
        axes[i].set_title(f"{season}", fontsize = 18, fontweight='bold')
        if i == 0:
            axes[i].set_ylabel("Sea Ice Extent: Arctic", fontsize=16)
        else:
            axes[i].set_ylabel("")
        axes[i].set_xlabel("")
        axes[i].set_xlim([1,16])
        lines = axes[i].get_lines()
        lines[0].set_color('red')
        lines[1].set_color('grey')
        axes[i].legend(handles=lines, labels = names_list, title="", fontsize = 14, frameon=False)
    for i, season in enumerate(seasons):
        j=i+4
        print(j)
        # Select the specific season and average it
        data_season = ds.sel(pole = 'SH', time=ds.time.dt.season == season).mean(dim='time')
        # Plot on the specific axis
        data_season['extent'].plot(ax=axes[j], x='forecast_day', hue='name', linewidth = 3, marker='o')
        axes[j].set_title("")
        if i == 0:
            axes[j].set_ylabel("Sea Ice Extent: Antarctic", fontsize=16)
        else:
            axes[j].set_ylabel("")
        axes[j].set_xlabel("Forecast Day", fontsize=16)
        #axes[j].legend(title="")
        axes[j].set_xlim([1,16])
        lines = axes[j].get_lines()
        lines[0].set_color('red')
        lines[1].set_color('grey')
        axes[j].legend(handles=lines, labels = names_list, fontsize = 14, title="", frameon=False)

    # Add a single colorbar for the whole figure
    plt.tight_layout()
    plt.savefig('test.png', dpi=600, bbox_inches='tight')

