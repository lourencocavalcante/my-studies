import os
import numpy as np
import xarray as xr

def readData(date):
    
    path = '../data/radar/'
    interval = len(os.listdir(path+str(date)))
    
    first_file = path+str(date)+'/'+str(os.listdir(path+str(date))[0])
    fxds = xr.open_dataset(first_file)
    lon = fxds.lon0.data
    lat = fxds.lat0.data
    
    # Original grid dimensions
    nx = 241
    ny = 241

    # pixel size (in meters)
    dx = 1000.
    dy = 1000.

    downsizeby = 1    

    # Compute grid dimensions and grid coordinates after resampling
    dx2, dy2 = dx*downsizeby, dy*downsizeby
    nx2, ny2 = int(nx/downsizeby), int(ny/downsizeby)

    X2, Y2 = np.meshgrid( np.arange(0,nx2*dx2, dx2), np.arange(0,ny2*dy2, dy2) )

    # Define container
    frames = np.zeros( (interval, nx2, ny2 ) )    
    
    for i in range(interval):
        d = str(path)+str(date)+'/'
        file = (sorted(os.listdir(path+str(date)))[i])
        xds = xr.open_dataset(d+file)
        rr = xds.rain_rate
        frames[i] =  rr
        
    return frames,lat,lon

