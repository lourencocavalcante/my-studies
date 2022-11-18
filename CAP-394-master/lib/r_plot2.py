my_coords = [-3.148556, -59.992000]     ## RADAR T1 SIPAM COORDS
zoom_scale = 2.2                        ## ZOOM SCALE

bbox = [my_coords[0]-zoom_scale,my_coords[0]+zoom_scale,\
         my_coords[1]-zoom_scale,my_coords[1]+zoom_scale]


fig, axes = plt.subplots(nrows=1,ncols=1,figsize=(10,10),dpi=100)
label = 'Rain rate in ' + runit+ ''
title = 'SIPAM Manaus S-Band Radar :' + str(date_time)

# draw filled contours.
clevs = [0, 1, 2.5, 5, 7.5, 10, 15, 20, 30, 40,
             50, 70, 100]

cmap_data = [(1.0, 1.0, 1.0),
                 (0.3137255012989044, 0.8156862854957581, 0.8156862854957581),
                 (0.0, 1.0, 1.0),
                 (0.0, 0.8784313797950745, 0.501960813999176),
                 (0.0, 0.7529411911964417, 0.0),
                 (0.501960813999176, 0.8784313797950745, 0.0),
                 (1.0, 1.0, 0.0),
                 (1.0, 0.6274510025978088, 0.0),
                 (1.0, 0.0, 0.0),
                 (1.0, 0.125490203499794, 0.501960813999176),
                 (0.9411764740943909, 0.250980406999588, 1.0),
                 (0.501960813999176, 0.125490203499794, 1.0),
                 (0.250980406999588, 0.250980406999588, 1.0)]

cmap = mcolors.ListedColormap(cmap_data, 'precipitation')
norm = mcolors.BoundaryNorm(clevs, cmap.N)
ax = axes

m = Basemap(projection='merc',llcrnrlat=bbox[0],urcrnrlat=bbox[1],\
                llcrnrlon=bbox[2],urcrnrlon=bbox[3],lat_ts=10,resolution='i')

## PRECIPTACAO
xi, yi = m(lon, lat)
## SIPAM RADAR
xm, ym = m(my_coords[1],my_coords[0])
radar = m.plot(xm,ym, marker='^',color='r', label='RADAR')


for cent in range(len(centroid)):
    clat, clon, mm_f = centroid[cent]['LAT'].item(),centroid[cent]['LON'].item(),centroid[cent]['RAIN_FALL'].item()

    t3x,t3y = m(clon, clat)
    m.plot(t3x,t3y, marker=markers.CARETDOWN, markersize=10, color='k')
    #plt.annotate(str(mm_f)[0:5]+'mm/h', xy=(t3x,t3y),xytext=(t3x+12,t3y+12),rotation=45, size=10)
    
m.plot(xm,ym, label='Nº Clusters: ' +str(len(centroid)),marker=markers.CARETDOWN, color='k')

cs = m.pcolormesh(xi,yi,frames[time], cmap = cmap, norm = norm, ax=ax)

# # # # Add Grid Lines
m.drawparallels(np.arange(bbox[0],bbox[1],(bbox[1]-bbox[0])/5),labels=[1,0,0,0],rotation=45, size=(7))
m.drawmeridians(np.arange(bbox[2],bbox[3],(bbox[3]-bbox[2])/5),labels=[0,0,0,1],rotation=45, size=(7))
m.drawmapboundary(fill_color='gray')

m.drawcoastlines()
m.drawstates()
m.drawcountries()
#m.fillcontinents(color='#FAFAFA',lake_color='dodgerblue')
#m.drawlsmask(land_color='Linen', lake_color='#CCFFFF')
m.drawrivers(color = '#0043CB', linewidth=1)

#m.readshapefile('./data/am_municipios/13MUE250GC_SIR', 'teste')
# # # # Add Colorbar
cbar = m.colorbar(cs, location='bottom', pad="10%")
cbar.set_label(label)

# # # # # Add Title
plt.title(title)
plt.legend()
plt.ylabel('Longitude', labelpad=40)
plt.xlabel('Latitude', labelpad=60)

plt.savefig('radar_image/'+ sorted(os.listdir(path+str(day)))[time]+'.png')

plt.show()