# RUN ON SERVER USING NEP CONDA ENVIRONMENT


from netCDF4 import Dataset
import pandas as pd
import numpy as np
import pickle
import matplotlib.animation as animation
import h5py
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy
import tqdm
import datetime
import os
from ll_xy import lonlat_to_xy

filename = 'svalbard_edge_coords_maxlon_40.h5'

ease_z = pickle.load(open('pickles/bath.p','rb'))

def get_coords(conc_dir):

    """
    Provides longitude, latitude, x & y coordinates of a polar stereographic grid (EPSG3408)
    """
    f=f'{conc_dir}/2020/ice_conc_nh_ease2-250_icdr-v2p0_202002051200.nc'
    with Dataset(f) as d:
        lon_grid = np.array(d['lon'])
        lat_grid = np.array(d['lat'])


        
    # Convert to EPSG 3408

    x_grid,y_grid = lonlat_to_xy(lon_grid,lat_grid,hemisphere='n')

    return (lon_grid,lat_grid,x_grid,y_grid)
    
def key_to_date(key):
    dstr = key.split('_')[-2]
    dt = datetime.date(int(dstr[:4]),
                  int(dstr[4:6]),
                  int(dstr[6:8]),
                  )
    return dt

conc_dir = '/Data/romal7177/ResearchData/IFT/EarthObservation/SatelliteAltimetry/OSISAF Sea Ice Concentration'
lon_grid,lat_grid,x_grid,y_grid = get_coords(conc_dir)

with h5py.File(f'edge_data/{filename}') as f:
    keys = sorted(list(f.keys()))


for year in np.arange(1983,2026):
    print(year)

    proj = ccrs.NorthPolarStereo()
    fig, ax = plt.subplots(1,1,figsize=(6,6),subplot_kw={'projection':proj})

    ax.set_extent([-0.1e6, 0.85e6, -2e6, -0.4e6], crs=ccrs.NorthPolarStereo()) 
    ax.add_feature(cartopy.feature.LAND, edgecolor='black',zorder=1)

    anno = ax.annotate(f'',
                fontsize='x-large',xy=(0.01,0.99),va='top',ha='left',xycoords='axes fraction',color='white')
    # COM = ax.plot([],[],transform=cartopy.crs.epsg('3408'),label=year,color=color,marker='^')
    l, = ax.plot([],[],transform=cartopy.crs.epsg('3408'),color='r')
    s = ax.scatter([],[],transform=cartopy.crs.epsg('3408'),s=200,marker='^',color='r')

    mesh = ax.pcolormesh(np.array(lon_grid), np.array(lat_grid), np.array(ease_z)/1000, vmin = -4, vmax = 0,
                        transform=ccrs.PlateCarree(),zorder=0,cmap='gray',alpha=0.8)

    cb = fig.colorbar(mesh)
    cb.set_ticks(np.arange(-4,0.1,1))
    cb.set_label('Water Depth (km)',fontsize='x-large')
    ax.set_title(year,fontsize='x-large')
    #ax.legend(loc='lower left')
    
    mykeys = [k for k in keys if str(year) in k]
    
    dts = []
    for key in mykeys:
        dts.append(key_to_date(key))



    def animate(i):
        anno.set_text(f'DOY = {dts[i].timetuple().tm_yday}')
        df = pd.read_hdf(f'edge_data/{filename}',key=mykeys[i])
        s.set_offsets([np.nanmean(df['x']),np.nanmean(df['y'])])
        l.set_ydata(df['y'])
        l.set_xdata(df['x'])

        return(l,s)

    plt.tight_layout()

    ani = animation.FuncAnimation(fig,
                                  animate,
                                  frames=range(len(mykeys)),
                                  #frames=range(10),
                                  )

    writer = animation.FFMpegWriter(
        fps=10, metadata=dict(artist='Me'), bitrate=1800)
    ani.save(f"animations/40lon/{year}.mp4", writer=writer)

    f=f'animations/40lon/{year}.gif'

    writer = animation.PillowWriter(fps=5,
                                    metadata=dict(artist='Robbie Mallett'),
    #                                 bitrate=1800,
                                    )
    ani.save(f, writer=writer)
    
    plt.close()
