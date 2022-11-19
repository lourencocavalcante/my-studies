import os, fnmatch
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
# import rasterio as rio
from mpl_toolkits.basemap import Basemap


# combines channels 2 and 3 to generate ndvi image
os.chdir("/home/wesley/Desktop/G16.SP_Bandas_2_3--L1B/ascii/")
listOfFiles = os.listdir('.')
pattern = "*SP_Bandas_2_3--L1B.pic*"
# print(listOfFiles)

entrys = []
for entry in listOfFiles:
    if entry not in entrys:
        entrys.append(entry[0:-8])
        # print(entry)

for i in entrys:
    i = '201907191720G16.SP_Bandas_2_3--L1B'
    band3 = pd.read_csv(i + '.C03.txt', header=None)
    band2 = pd.read_csv(i + '.C02.txt', header=None)
    ndvi = (band3 - band2)/(band2 + band3)
    # ndvi = np.flipud(ndvi)
    print(i)
    # fig = plt.imshow(ndvi)
    # plt.axis('off')
    # fig.axes.get_xaxis().set_visible(False)
    # fig.axes.get_yaxis().set_visible(False)
    # # print(type(ndvi[0][1]))
    # # dataframe = ndvi.DataFrame(data=mat.astype(float))
    # # ndvi.to_csv(i + '_NDVI.txt', sep=',', header=False, float_format='%.2f', index=False)
    # plt.savefig(i + '.png', format='png', bbox_inches='tight', pad_inches = 0, dpi=1000) # high pixel density
    # # plt.savefig(i + '.png', format='png', bbox_inches='tight', pad_inches = 0)
    break

# import numpy as np

# netcdf info
# OrderedDict([('MINLON', -53.5), ('MAXLON', -44.0), ('MINLAT', -25.5), ('MAXLAT', -19.5), ('DATA_MINLON', -53.5), ('DATA_MAXLON', -44.0), ('DATA_MINLAT', -25.5), ('DATA_MAXLAT', -19.5), ('COVER', 100.0), ('RESOLUTION', 0.005), 
# ('NLON', 2109), ('NLAT', 1332), ('BPP', 2), ('NCHAN', 4), ('DATETIME', 'ء�'), ('PRODUCT', ''), ('SETUP', ''), ('SATELLITE', 'ء�'), ('CHANNELS', ' C01,C02,C03,C05'), ('SEPARATOR', 'h�\x04\x08X���\\j�')])


# Choose the visualization extent (min lon, min lat, max lon, max lat)
extent = [-53.50, -25.50, -44.0, -19.50]
minlon = extent[0]; maxlon = extent[2]; minlat = extent[1]; maxlat = extent[3]

# Get the latitudes
nlat = 1332
steplat = abs(minlat - maxlat)/nlat
lats = np.arange(minlat, maxlat, steplat, dtype='float')

# Get the longitudes
nlon = 2019
steplon = abs(maxlon - minlon)/nlon
lons = np.arange(minlon, maxlon, steplon, dtype='float')

# latitude lower and upper index
latli = np.argmin(np.abs(lats - extent[1]))
latui = np.argmin(np.abs(lats - extent[3]))

# longitude lower and upper index
lonli = np.argmin(np.abs(lons - extent[0]))
lonui = np.argmin(np.abs(lons - extent[2]))

# Extract the Brightness Temperature / Reflectance values from the NetCDF
# data = nc.variables['Band1'][ latli:latui , lonli:lonui ]

# Flip the y axis, divede by 100
# data = (np.flipud(data) / 100)

# Define the size of the saved picture ==============================================================
DPI = 100
# ax = plt.figure(figsize=(nlon, nlat), frameon=False, dpi=DPI)
ax = plt.figure(figsize=(nlon/float(DPI), nlat/float(DPI)), frameon=False, dpi=DPI)
#====================================================================================================

# Plot the Data =====================================================================================
# Create the basemap reference for the Rectangular Projection
bmap = Basemap(llcrnrlon=extent[0], llcrnrlat=extent[1], urcrnrlon=extent[2], urcrnrlat=extent[3], epsg=4326, resolution='f')

# Draw the countries and Brazilian states shapefiles
# bmap.readshapefile('/Scripts/GEONETCast/Shapefiles/BRA_adm1','BRA_adm1',linewidth=0.50,color='cyan')
# bmap.readshapefile('/Scripts/GEONETCast/Shapefiles/ne_10m_admin_0_countries','ne_10m_admin_0_countries',linewidth=0.50,color='cyan')

# Plot the GOES-16 channel with the converted CPT colors (you may alter the min and max to match your preference)
fig = bmap.imshow(ndvi)


plt.axis('off')
fig.axes.get_xaxis().set_visible(False)
fig.axes.get_yaxis().set_visible(False)
plt.savefig('/home/wesley/Desktop/ndvi' + '.png', dpi=DPI, bbox_inches='tight', pad_inches=0)