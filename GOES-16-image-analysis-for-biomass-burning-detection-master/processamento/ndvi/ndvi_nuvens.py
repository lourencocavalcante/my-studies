import os, fnmatch
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
# import rasterio as rio
from mpl_toolkits.basemap import Basemap

pattern = "SP_Bandas_2_3--L1B.pic.C02"
path = "/run/media/wesley/6CD80ADD0368A759/Cepagri/goes_server/ascii/"
path_save = "/run/media/wesley/6CD80ADD0368A759/Cepagri/ndvi/"

def Dates(path, pattern):
    """
    Returns file dates of all filenames matching pattern
    """
    files = sorted(os.listdir(path))
    dates = []
    for file in files:
        if pattern in file and file[0:-36] not in dates:
            dates.append(file[0:-36])
    return(sorted(dates, reverse=True))

def Files(path, date, pattern):
    files_all = sorted(os.listdir(path))
    filenames = []
    for file in files_all:
        if pattern in file and date in file:
            filenames.append(file[0:-8])
    return filenames

def NDVI_out(path, files):
    ndvi = []
    for file in files:
        global file_global
        file_global = file
        band2 = np.genfromtxt(path + file + ".C02.txt", delimiter=',')
        band3 = np.genfromtxt(path + file + ".C03.txt", delimiter=',')
        # print(band2.shape)
        # print(file)
        # print(len(ndvi))
        if len(ndvi)==0:
            print("--", file[0:4] + '.' + file[4:6] + '.' + file[6:8] + ' ' + file[8:10] + ':' + file[10:12])
            ndvi = np.divide(np.subtract(band3,band2), np.add(band3, band2))
        else:
            ndvi_new = np.divide(np.subtract(band3,band2), np.add(band3, band2))
            ndvi = np.fmax(ndvi, ndvi_new)
            print(file[0:4] + '.' + file[4:6] + '.' + file[6:8] + ' ' + file[8:10] + ':' + file[10:12])
    np.savetxt(path_save +  file_global[0:4] + "_" + file_global[4:6] + "_" + file_global[6:8] + "_" + file_global[8:10] + "_NDVI.txt", ndvi)
    return(ndvi)
    # np.savetxt(path + file[0:15] + '.NDVI.txt', ndvi)
    # print(file[0:15] + '.NDVI.txt' + ' saved!')
    # for file in files:
    #     os.remove(path + file + ".C02.txt")
    #     os.remove(path + file + ".C03.txt")

for date in Dates(path, pattern):
    ndvi = NDVI_out(path, Files(path, date, pattern))

#     # Choose the visualization extent (min lon, min lat, max lon, max lat)
#     extent = [-53.50, -25.50, -44.0, -19.50]
#     minlon = extent[0]; maxlon = extent[2]; minlat = extent[1]; maxlat = extent[3]

#     # Get the latitudes
#     nlat = 1332
#     steplat = abs(minlat - maxlat)/nlat
#     lats = np.arange(minlat, maxlat, steplat, dtype='float')

#     # Get the longitudes
#     nlon = 2019
#     steplon = abs(maxlon - minlon)/nlon
#     lons = np.arange(minlon, maxlon, steplon, dtype='float')

#     # latitude lower and upper index
#     latli = np.argmin(np.abs(lats - extent[1]))
#     latui = np.argmin(np.abs(lats - extent[3]))

#     # longitude lower and upper index
#     lonli = np.argmin(np.abs(lons - extent[0]))
#     lonui = np.argmin(np.abs(lons - extent[2]))

#     # Extract the Brightness Temperature / Reflectance values from the NetCDF
#     # data = nc.variables['Band1'][ latli:latui , lonli:lonui ]

#     # Flip the y axis, divede by 100
#     # data = (np.flipud(data) / 100)

#     # Define the size of the saved picture ==============================================================
#     # ax = plt.figure(figsize=(nlon, nlat), frameon=False) # full size
#     DPI = 100
#     ax = plt.figure(figsize=(nlon/float(DPI), nlat/float(DPI)), frameon=False, dpi=DPI)
#     #====================================================================================================

#     # Plot the Data =====================================================================================
#     # Create the basemap reference for the Rectangular Projection
#     bmap = Basemap(llcrnrlon=extent[0], llcrnrlat=extent[1], urcrnrlon=extent[2], urcrnrlat=extent[3], epsg=4326, resolution='h')
#     fig = bmap.imshow(ndvi)

#     plt.axis('off')
#     fig.axes.get_xaxis().set_visible(False)
#     fig.axes.get_yaxis().set_visible(False)
#     # plt.savefig(path_save + file_global + '.png', dpi=DPI, bbox_inches='tight', pad_inches=0)
#     print("============ " + file_global[0:4] + '.' + file_global[4:6] + '.' + file_global[6:8] + ' ' + file_global[8:10] + " salva! ============")
#     # ndvi = np.round(ndvi, decimals=9)
#     np.savetxt(path_save +  file_global[0:4] + "_" + file_global[4:6] + "_" + file_global[6:8] + "_" + file_global[8:10] + "_NDVI.txt", ndvi)
#     ax.clear()
#     plt.close(ax)
