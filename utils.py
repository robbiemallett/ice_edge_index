from netCDF4 import Dataset
from ll_xy import lonlat_to_xy
import numpy as np
from shapely.geometry import LineString
from contourpy import contour_generator
import pandas as pd
import pickle

spitsbergen_mask=pickle.load(open('svalbard_mask.p','rb'))


def get_multi_COM(data_dir,file_name,date,lon_grid,lat_grid,x_grid,y_grid,
                  minlon=0,maxlon=40,thresh_array=np.arange(10,91,10),
                  output_lines=False):

    """
    Delivers the mean x & y coordinates of an ice edge for multiple thresholds based on a netcdf
    """
    
    with Dataset(f'{data_dir}/{date.year}/{file_name}') as d:
        
        xbars=[]
        ybars=[]

        for thresh in thresh_array:
            
            try:

                #   old
                # lines,line_lengths,open_lines = get_contours(d,lon_grid,lat_grid,xgrid,ygrid,
                #                                   minlon=minlon,maxlon=maxlon,thresh=thresh)
                # lines = [l for l,o in zip(lines,open_lines) if o==1]
                # line_lengths = [l for l,o in zip(line_lengths,open_lines) if o==1]
                # longest_line = lines[np.argmax(line_lengths)]

                lines1, line_lengths1, open_cont1 = get_contours(d,lon_grid,lat_grid,
                                                                 x_grid,y_grid,clever=True,
                                                                 thresh=thresh)
                lines2, line_lengths2, open_cont2 = get_contours(d,lon_grid,lat_grid,
                                                                 x_grid,y_grid,clever=False,
                                                                 thresh=thresh)

                lines1 = [l for l,o in zip(lines1,open_cont1) if o==1]
                line_lengths1 = [l for l,o in zip(line_lengths1,open_cont1) if o==1]

                lines2 = [l for l,o in zip(lines2,open_cont2) if o==1]
                line_lengths2 = [l for l,o in zip(line_lengths2,open_cont2) if o==1]

                longest_line1 = lines1[np.argmax(line_lengths1)]
                longest_line2 = lines2[np.argmax(line_lengths2)]

                if len(longest_line1)>len(longest_line2):
                    longest_line=longest_line2
                else:
                    longest_line=longest_line1


                x = longest_line[:,0]
                y = longest_line[:,1]
                lonline,latline=lonlat_to_xy(x,y,hemisphere='n',inverse=True)
    
                xclean = x[((lonline>minlon) & (lonline<maxlon))&(latline<88)]
                yclean = y[((lonline>minlon) & (lonline<maxlon))&(latline<88)]
    
                xbar,ybar,x_,y_ = calc_line_COM(xclean,yclean)

                if output_lines: 
                    df = pd.DataFrame({'x':xclean,
                                       'y':yclean})
                    datestr = f'{date.year}{str(date.month).zfill(2)}{str(date.day).zfill(2)}'
                    df.to_hdf(f'edge_data/edge_coords.h5',
                              key=f'coords_{datestr}_{thresh}',
                              mode='a')

                
            except Exception as e:
                
                print(e)
                print(file_name)
                xbar,ybar=np.nan,np.nan
            
            xbars.append(xbar)
            ybars.append(ybar)
    
    return (xbars,ybars)

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

def mask_channels(it):

    #hinlopenstretet
    if (it[260,361]) and (it[258,229]):
        it[258:260,#down
        230]=1#across
        it[259,#down
        231]=1#across
    #barentsoya
    if (it[262,234]) and (it[264,233]):
        it[263,233:235]=1
    return it

def get_contours(d,
                 lon_grid,lat_grid,
                 xgrid,ygrid,
                 minlon=0,maxlon=38,thresh=50,maxlat=87,clever=False):
    
    it = np.array(d['ice_conc'][0]).astype(np.float32)
    it[it<=thresh] = 0
    it[it>thresh] = 1

    it[lon_grid>maxlon]=np.nan
    it[lon_grid<minlon]=np.nan
    it[lat_grid>maxlat]=np.nan

    it = mask_channels(it)


    if clever: it[spitsbergen_mask==1] = 1

    cont_gen = contour_generator(z=it,x=xgrid,y=ygrid)

    lines = cont_gen.lines(0.5)
    
    line_lengths = [len(l) for l in lines]
    
    open_cont=[]
    for line in lines:
        x0,y0=line[0,0],line[0,1]
        x1,y1=line[-1,0],line[-1,1]
        if (np.abs((x1-x0)) < 10_000) or (np.abs((y1-y0)) < 10_000):
            open_cont.append(0)
        else:open_cont.append(1)
        
    return lines,line_lengths,open_cont


def calc_line_COM(x,y):
    
    line = LineString(np.array([x,y]).T)

    distance_delta=5000
    distances = np.arange(0,line.length,distance_delta)

    points = [line.interpolate(distance) for distance in distances]
    new_line = LineString(points)
    
    x_ = np.array(new_line.coords)[:,0]
    y_ = np.array(new_line.coords)[:,1]

    xbar = np.nanmean(x_)
    ybar = np.nanmean(y_)
    
    return(xbar,ybar,x_,y_)
