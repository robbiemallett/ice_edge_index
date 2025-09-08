#SHOULD BE RUN IN ice_edge SCREEN on server
#SHOULD BE RUN IN ice_edge CONDA ENVIRONMENT (SEE environment_b.yml)

#sshfs romal7177@rcm3.phys.uit.no:/ /home/robbie/uit_mnt -o nonempty
#ssh romal7177@rcm3.phys.uit.no



from netCDF4 import Dataset
import pandas as pd
import numpy as np
from ll_xy import lonlat_to_xy
import tqdm
import os
import datetime
from utils import get_coords, get_multi_COM

root_dir=''
# root_dir=''
research_data=f'{root_dir}/Data/romal7177/ResearchData'
conc_dir = f'{research_data}/IFT/EarthObservation/SatelliteAltimetry/OSISAF Sea Ice Concentration'

lon_grid,lat_grid,xgrid,ygrid = get_coords(conc_dir=conc_dir)

years_available = [int(x) for x in sorted(os.listdir(conc_dir))]

filenames = []
dts = []
years = []

for yr in years_available:
    fnames = sorted(os.listdir(f'{conc_dir}/{yr}'))
    filenames += fnames
    dts += [datetime.date(int(dtstr[-15:-11]),int(dtstr[-11:-9]),int(dtstr[-9:-7])) for dtstr in fnames] 
    years += [yr]*len(fnames)
    
df = pd.DataFrame({'filename':filenames,'date':dts,'year':years})
df['month'] = [x.month for x in df['date']]
df['day'] = [x.day for x in df['date']]

thresh_array = np.arange(10,91,20)
maxlon=50

for year in sorted(list(set(df['year']))):

    print(year)
    
    df_yr = df[df['year']==year].iloc[:]

    xb=[];yb=[]

    for f, dt in tqdm.tqdm(list(zip(df_yr['filename'],df_yr['date']))):

        xbars,ybars = get_multi_COM(conc_dir,f,dt,
                                    lon_grid,lat_grid,
                                    xgrid,ygrid,
                                    maxlon=maxlon,
                                    thresh_array=thresh_array,
                                    output_lines=True)
        xb.append(xbars)
        yb.append(ybars)
    
    xb=np.array(xb)
    yb=np.array(yb)
    
    for i,thresh in zip(range(len(thresh_array)), thresh_array):
        # Convert lon/lats to x/y and set as new column of dataframe to be saved
        df_yr[f'lon_{thresh}'], df_yr[f'lat_{thresh}'] = lonlat_to_xy(xb[:,i],yb[:,i],
                                                                          hemisphere='n',inverse=True)

    # Save out dataframe
    df_yr.to_csv(f'edge_data/ice_edge_{year}_maxlon_{maxlon}_Sep25.csv')
