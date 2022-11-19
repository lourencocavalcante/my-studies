#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 17 21:07:12 2021

@author: felos
"""
import os
import re
import s3fs
import math
import time
import datetime
from   datetime import date, datetime , timedelta

import numpy  as np
import pandas as pd
import scipy.ndimage
import matplotlib.pyplot as plt

from PIL    import Image
from ftplib import FTP
from matplotlib        import cm
from matplotlib.colors import ListedColormap

from pathlib import Path
from pyproj  import Proj
import h5py

# Funciones auxiliares -------------------------------------------------------

def degree2rad(degree):
    """Pasa de grados a radianes."""
    k   = math.pi / 180
    rad = degree*k
    return rad

def rad2degree(rad):
    """pasa de radianes a grados."""
    k     = 180 / math.pi
    degree = rad*k 
    return degree

# FUNCIONES AUXILIARES PARA EL PLOTEO. -------------------------------------

def Contraste(array,contraste):
    """ Función de contraste para las imágenes del GOES,
        útil solo para visualización ! 

        !! Función experimental que posiblemente cambie a futuro.
    """

    array = array / 255                           # Normalizamos pixeles
    array = np.exp(-array*contraste)              # Aplicamos función del contraste
    array = abs(array - 1)                        # Arregleamos el flip 
    array = array*255    
    return array


# FUNCIONES AUXILIARES PARA EL USO DEL FTP EN LA DESCARGA DESDE LOS SERVIDORES
# DE CLASS DE LA NOAA. -------------------------------------------------------------

def obtenerListaArchivos_FTP(ftp_object):
    " Obtiene una lista con los archivos en el directorio actual del ftp."

    lista_detalles_archivos  = []

    def añadirLista(string):
        "callback para ftp.retrlines,añade a una lista el nombre de cada archivo."

        lista_detalles_archivos.append(string)
    # mediante el callback añadimos ls nombres de cada archivo a la lista
    ftp_object.retrlines('LIST',callback=añadirLista)
    # la lista contiene ademas de los nombres, detalles extra como permisos o fecha, filtramos el nombre.
    lista_nombres = []
    for detalle in lista_detalles_archivos:
        nombre_archivo = detalle.split(" ")[-1]
        lista_nombres.append(nombre_archivo)
    
    return lista_nombres

def descargaArchivo_FTP(ftp_object,nombre_archivo,nombre_output,verbose=False):
    " Realiza la descarga desde el servidor FTP dado el nombre del archivo. "
    with open(nombre_output,"wb") as archivo:
        if verbose:
            print(ftp_object.retrbinary('RETR ' + nombre_archivo, archivo.write))
        else:
            ftp_object.retrbinary('RETR ' + nombre_archivo, archivo.write)


#------------------------------------------------------------------------------

def descargarOrden_CLASS(num_orden,verbose=False,path_salida=""):
    """ Descarga una orden soliciada al sitio CLASS de la NOAA
        Requiere haber solicitado la ordeen antes y que esta esté
        lista.

        Se accede a la descarga de estos datos con el número de orden
        inidicado por el servido, desde la plataforma o por correo
        electrónico.
    """
    
    # FALTA IMPLEMENTAR UN CONTADOR DE DESCARGAS PARA DESCARGAS GRANDES.
    
    url_base = "ftp.avl.class.noaa.gov"
    # Iniciamos conexión
    ftp      = FTP(url_base)
    ftp.login()
    # Entramos al directorio
    path = str(num_orden) + "/001"
    ftp.cwd(path)
    # Obtenemos lista de los archivos
    lista_nombres = obtenerListaArchivos_FTP(ftp)
    # Iniciando descarga de los archivos.
    for nombre_archivo in lista_nombres:
        descarga_correcta = False
        while descarga_correcta == False:
            try:
                descargaArchivo_FTP(ftp,nombre_archivo,path_salida + nombre_archivo,verbose=verbose)
            except:
                print("Descarga incorrecta volviendolo a intentar ...")
                time.sleep(5)
            else:
                descarga_correcta = True
    print("Descarga completada!")


def obtenerFecha_GOES(nc,return_datetime=False):
    """ Devuelve un string con la fecha de la imágen.
        
        return_datetime (bool): Si está en True, devuelve
        .. la fecha como objeto datetime. De lo contrario
        .. lo devuelve como string.

        !! Falta hacer que devuelva la hora en formato de 24h

        !! Falta implementar que de la hora para otras zonas
        horarias.
    """
    
    if type(nc) == int: 
        t = nc
    else:
        # Obtiene los segundos desde 2000-01-01 12:00
        try:
            t = float(np.array(nc.variables["t"]))
        except:
            t = float(np.array(nc.variables["time"])[0])

    # Con ayuda de la librería "datetime" obtenemos la fecha actual.
    fecha_inicio = datetime(2000,1,1,12,0,0)
    time_delta   = timedelta(seconds=t)
    fecha        = fecha_inicio + time_delta
    if return_datetime:
        return fecha
    else:
        formato      = "%Y-%m-%d_%H-%M"
        return fecha.strftime(formato)

def obtenerBanda_GOES(nc):
    """ Obtiene de que banda es el archivo nc correspondiente a el producto de
        Radiation """
    
    id_banda = np.array(nc.variables["band_id"])
    id_banda = int(id_banda)
    
    return id_banda


def irradiancia2temperatura_GOES(array,nc):
    """Pasa de los valores de irradiancia a grados 
    centígrados para las bandas emisoras"""
    
    fk1 = float(np.array(nc.variables["planck_fk1"]))
    fk2 = float(np.array(nc.variables["planck_fk2"]))
    bc1 = float(np.array(nc.variables["planck_bc1"]))
    bc2 = float(np.array(nc.variables["planck_bc2"]))
    
    a = np.log(1 + (fk1 / array))
    b = (fk2 / a - bc1)
    
    resultado  = b / bc2
    
    return resultado


def px2coordinates_GOES(nc,px_x,px_y):
    """Pasa de pixeles en la imágen a coordenadas."""
    
    # Parámetros del satélite.
    
    # Fixed Grid scanning angles.
    X = nc.variables["x"]
    Y = nc.variables["y"]
    # Longitud of proyection of the origin
    lambda_o = nc.variables["goes_imager_projection"].longitude_of_projection_origin
    lambda_o = degree2rad(lambda_o)
    # Semi major axis value
    r_eq   = 6378137          # [m]
    # Semi minor axis value
    r_pool = 6356752.31414    # [m]
    # Satellite Hight from center of earth [m]
    H      = 42164160         # [m]
    
    # Cálculos previos.
    frac_r = r_eq / r_pool
    
    coef1  = frac_r**2
    
    x = X[px_x]
    y = Y[px_y]
    
    cosx = math.cos(x)
    cosy = math.cos(y)
    sinx = math.sin(x)
    siny = math.sin(y)
    
    a = sinx**2 + (cosx**2)*(cosy**2 + coef1*siny**2)
    b = -2*H*cosx*cosy
    c = H**2 - r_eq**2
    
    r_s = (-b-math.sqrt(b**2 - 4*a*c)) / 2*a
    
    s_x =  r_s*cosx*cosy
    s_y = -r_s*sinx
    s_z =  r_s*cosx*siny
    
    coef2 = s_z / math.sqrt((H-s_x)**2 + s_y**2)
    
    coef3 = s_y / (H-s_x)
    
    latitud  = math.atan(coef1*coef2)
    longitud = lambda_o  - math.atan(coef3)
    
    # Pasamos de rads a grados.
    latitud  = rad2degree(latitud )
    longitud = rad2degree(longitud)
    
    return latitud , longitud

def coordinates2px_GOES(nc,latitud,longitud):
    """Pasa de coordenadas a localización en px."""
    # Parámetros del satélite.

    # Alternativa rápida a no tener que dar el nc.
    try:
        X , Y , lambda_o = nc
    except TypeError:
        # Fixed Grid scanning angles.
        X = nc.variables["x"]
        Y = nc.variables["y"]
        # Longitud of proyection of the origin
        lambda_o = nc.variables["goes_imager_projection"].longitude_of_projection_origin
    
    lambda_o = degree2rad(lambda_o)
    # Semi major axis value
    r_eq   = 6378137          # [m]
    # Semi minor axis value
    r_pool = 6356752.31414    # [m]
    # Satellite Hight from center of earth [m]
    H      = 42164160         # [m]
    # exentricidad 
    e = 0.0818191910435
    
    # Pasamos de grados a radianes
    latitud  = degree2rad(latitud )
    longitud = degree2rad(longitud)
    
    # Cálculos intermedios
    coef1 = (r_pool / r_eq)**2
    
    phi_c = math.atan(coef1*math.tan(latitud))
    r_c   = r_pool / math.sqrt(1-(e*math.cos(phi_c))**2)
    
    s_x   = H - r_c*math.cos(phi_c)*math.cos(longitud-lambda_o)
    s_y   = -r_c*math.cos(phi_c)*math.sin(longitud -lambda_o)
    s_z   = r_c*math.sin(phi_c)
    
    # Revisamos la visiblidad desde el satélite.
    inequality1 = H*(H-s_x)
    inequality2 = s_y**2 + (s_z**2)*(r_eq/r_pool)**2
    message = f"Coordenada no visibles desde el satélite: {latitud},{longitud}"
    if inequality1 < inequality2:
        raise ValueError(message)
    
    # Obtenemos los ángulos delevación y escaneo N/S E/W.
    y = math.atan(s_z/s_x)
    x = math.asin(-s_y/math.sqrt(s_x**2 + s_y**2 + s_z**2))
    
    # De los ángulos de escaneo obtemos el pixel.
    
    # Si el array que contiene la variable X del .nc nos inidica que ángulo de escaneo le
    # ..  corresponde a cada pixel. ahora tenemos que encontrar "una situación inversa" , 
    # .. donde dado un ángulo de  escaneo en particular tenemos que encontrar su pixel. 
    # .. Esto no se puede hacer directo puesto que los ángulos de escaneo son números reales y la
    # .. posición de los pixeles se representa con enteros.
    # Para resolver este problema resto el ángulo de escaneo de nuestro interes con el array X, y
    # .. encuentro la posición o index del valor menor de esta diferencia.
    
    X_array = np.array(X)
    X_array = np.abs(X_array - x)
    px_x    = np.argmin(X_array)
    
    Y_array = np.array(Y)
    Y_array = np.abs(Y_array - y)
    px_y    = np.argmin(Y_array)
    
    return px_x , px_y

def plot_GOES(array,contraste,cmap="gray",nombre_output =""):
    "Apicación del contraste y guardado."
    
    if contraste != 0:                      
       array = Contraste(array,contraste)                      # Reescalamos
       
    plt.figure(figsize=(10,10))
    plt.imshow(array,cmap="gray")
    #plt.axis("on")
    plt.grid(True)
    
    if nombre_output != "":
        plt.savefig(nombre_output, bbox_inches=0)
        plt.close()
    

def cmap_banda13_GOES():
    """ Obtiene un custom c_map adecuado para la banda 13, 
        (escala de temperaturas)"""
    
    inicio = -110
    final  = 40
    dt     = final - inicio
    
    ini_gist_yarg = -110
    fin_gist_yarg = -78
    dy            = fin_gist_yarg - ini_gist_yarg
    
    ini_hsv = -78
    fin_hsv = -45
    dh = fin_hsv - ini_hsv
    
    ini_ocean = -45
    fin_ocean = -30
    do = fin_ocean - ini_ocean
    
    long_yarg = int(256*dy/dt)
    long_hsv  = int(256*dh/dt)
    long_do   = int(256*do/dt)
    long_db   = 256 - long_yarg - long_hsv - long_do
    
    gist_yarg = cm.get_cmap('gist_yarg', 256 )
    hsv       = cm.get_cmap('hsv'      , 256 )
    ocean     = cm.get_cmap("ocean"    , 256 )
    binary    = cm.get_cmap('binary'   , 256 )
    
    gist_yarg_parte  = gist_yarg(np.linspace(0,1,long_yarg  ))
    hsv_parte        =       hsv(np.linspace(0,0.29,long_hsv ))
    ocean_parte      =     ocean(np.linspace(0,1,long_do    ))
    binary_parte     =    binary(np.linspace(0.5,1,long_db    ))
    
    custom_cmap_array = np.concatenate([gist_yarg_parte,hsv_parte,ocean_parte,binary_parte])
    custom_cmap       = ListedColormap(custom_cmap_array)
    
    return custom_cmap
    
def cortarYcentrar_GOES(topo,x,y ,ventana=200):
    """
    Dado un par de pixeles (px_x , px_y) o coordenadas,
    obtiene un subarray cuadrado, de radio (ventana),
    a partir del array introducido (topo)
    """
    
    # Revisa que se respete los límites de la imágen.
    lim_izquierdo = max(x-ventana,0)
    lim_derecho   = min(x+ventana+1,topo.shape[1])
    lim_inferior  = max(y-ventana,0)
    lim_superior  = min(y+ventana+1,topo.shape[0])
    
    mensaje_aviso = "!! Aviso : Se ha alcanzado los límites de la imágen en el recorte, el resultado ya no será un array cuadrado."
    if lim_izquierdo == 0:
        lim_derecho = lim_izquierdo + ventana + 1
        print(mensaje_aviso)
        
    if lim_derecho == topo.shape[1]:
        lim_izquierdo = lim_derecho - ventana
        print(mensaje_aviso)
    if lim_inferior == 0:
        lim_superior = lim_inferior + ventana + 1
        print(mensaje_aviso)
    if lim_superior == topo.shape[0]:
        lim_inferior == lim_superior - ventana
        print(mensaje_aviso)
    if len(topo.shape) == 3:
        array = topo[ lim_inferior:lim_superior ,lim_izquierdo:lim_derecho,:]
    else:
        array = topo[ lim_inferior:lim_superior ,lim_izquierdo:lim_derecho]
    return array

def recorteYplot_GOES(array,centro_px,centro_py,ventana=200,contraste=5,cmap="gray",dir_guardado=""):
    "Recorte y centrado de la comunidad "
    array = cortarYcentrar_GOES(array,centro_px,centro_py,ventana)
    plot_GOES(array,contraste,dir_guardado,cmap=cmap)
    
  
def guardarPlot_GOES(array,centro_px,centro_py,dir_guardado,ventana=200,contraste=5):
    """" No usa matplotlib por lo que el guardado es más rápido y eficiente,
         solo produce imágenes es escala de grises. """

    array = cortarYcentrar_GOES(array,centro_px,centro_py,ventana)
    array = Contraste(array,contraste)    
    array = array.astype(dtype='uint8')  
    img = Image.fromarray(array)
    img.save(dir_guardado)


def latlonArray(nc,data_path="PreCompute/",enviar_0_0 = True):
    """ 
        Cálcula las coordenadas de cada pixel de la variable principal
        del netCDF. El resultado son 2 arrays uno que contiene la latitud
        y otro que contiene la longitud, estos arrays estan en la forma
        de meshgrid.
        
        Función muy útil para la realización de proyecciones.
        
        Revisa si existen los arrays lat lon precalculados,
        de no existir los crea, en la carpeta especificada en 
        la variable como data_path.
        
        enviar_0_0 : Los pixeles fuera de la Tierra por default son
        ... marcados como np.inf , esto puede causar problemas. En particular
        ... cuando se usa para generar un pcolormesh con la libería Basemap de
        ... plt_toolkit.
        ... Esta opción si es marcada como True, mapea los np.inf a 0 y los envia a
        ... las coordenadas 0.0 , 0.0 (Fuera del continente americano)
        
        """
    
    # Obtenemos el tamaño del array.
    x_shape = np.array(nc.variables["x"]).shape[0]
    y_shape = np.array(nc.variables["y"]).shape[0]
    
    shape = (y_shape,x_shape)
    
    # Generamos nombre.
    nombre_h5 =  data_path + f"latlon_CONUS_{shape[0]}_{shape[1]}.h5"
    
    # Creamos directorio si no existe.
    Path(data_path).mkdir(parents=True, exist_ok=True)
    
    # Buscamos en el path indicado.
    if os.path.exists(nombre_h5):
        with h5py.File(nombre_h5, "r") as file:
            lats = file["lats"][()]  # [()] <-- Para extraer los datos a np array.
            lons = file["lons"][()]
            file.close()
    # Si no existe,calculamos y guardamos.
    else:
        print("Aviso: No se encontró los arrays latlon, se calcularan unos nuevos.")
        # Obtenemos altura del satélite.
        sat_h = nc.variables['goes_imager_projection'].perspective_point_height
        # Obtenemos la longitud del satelite.
        sat_lon = nc.variables['goes_imager_projection'].longitude_of_projection_origin
        # Sweep del satélite ?? 
        sat_sweep = nc.variables['goes_imager_projection'].sweep_angle_axis
        
        # Obtenemos las coordenadas de la proyección geostacionaria.
        X = nc.variables['x']*sat_h
        Y = nc.variables['y']*sat_h
        # Calculamos los arrays.
        p = Proj(proj='geos', h=sat_h, lon_0=sat_lon, sweep=sat_sweep)
        XX, YY     = np.meshgrid(X, Y)
        lons, lats = p(XX, YY, inverse=True)

        # Mandamos a 0 los valores infinitos.
        # Dado que las coordendas 0.0,0.0 no estan en America, esta fuera de la vista,
        # ... y no afectara el cambio. Por otro lado si lo dejamos con valores infinitos
        # ... pcolormesh (para graficar los mapas) no funciona.
        if enviar_0_0:
            lons[lons == np.inf] = 0
            lats[lats == np.inf] = 0
        
        # Guardamos nuevos arrays antes de retornarlos.
        with h5py.File(nombre_h5, "w") as file:
            file.create_dataset("lats",data=lats)
            file.create_dataset("lons",data=lons)
    #lats,lons = lats.value , lons.value 
    return lats , lons


def preProcesado_WS(nc_WS):
    """
    Procesa los datos para la realización de un quiver plot.
    Devueve como lista las componentes de los vectores de viento
    junto con la lista de lat,lons.

    Ojo, son listas no son arrays !!
    """
    FILL_VALUE = -999.0
    lat = np.array(nc_WS.variables["lat"])
    lon = np.array(nc_WS.variables["lon"])
    ws  = np.array(nc_WS.variables["wind_speed"])
    wd  = np.array(nc_WS.variables["wind_direction"])
    
    if np.max(ws) == FILL_VALUE:
        print("Aviso: No hay valores validos de ws.")
        
    # Mandamos a 0 los valores inválidos.
    ws[ws == FILL_VALUE] = 0
    
    # Obtenemos las componentes de los vectores.
    wd = np.radians(360 - wd)
    ws_lat = -np.cos(wd)*ws
    ws_lon = np.sin(wd)*ws
    
    return lat,lon,ws_lat,ws_lon


# Funciones para el proecesamiento del wind-speed.----------------
def preProcesado_WS_Interpolación(nc_WS,nc_ref,dx=1,reducción=50,rellenar_faltantes=True):
    """
    Toma un archivo nc que contiene la información de la velocidad de viento, 
    y lo adapta a las dimenciones de los datos que estan en el archivo nc de 
    referencia proporcionado.
    
    Dado que el fromato en el que viene los datos es de lista, hay que buscar,
    dato por dato las coordenadas mas cercanas a las que pertenece. Las coordenadas
    tomadas son las de la variable dentro del nc de referencia.
    
    dx: Máxima distancia (en grados de coordenadas) de asignación de un valor de 
    ... velocidad de viento a una coordenada.
    
    reducción (int): Escala de reducción de tamaño del array de referencia. 
    ... Dado el costo computacional del proceso, es necesario reducir las
    ... dimenciones del array de referencia durante la asignación de valores.
    ... Al final de proceso de asignación se vuelve a escalar el array.
    
    rellenar_faltantes: Se quitan los ceros, resultado de valores invalidos y se rellena 
    ... con el valor válido más cercano, dentro de un readio de (dx) grados.
    """
    
    # PASO 1: Obtenemos las coordenadas y la información de cálidad de cada elemento.

    lat_WS = np.array(nc_WS.variables["lat"])
    lon_WS = np.array(nc_WS.variables["lon"])

    flag_list = np.array(nc_WS.variables["DQF"])

    ws_list = np.array(nc_WS.variables["wind_speed"])
    wd_list = np.array(nc_WS.variables["wind_direction"]) 

    # Quitamos los valores de relleno (._fill_values)
    ws_list[ws_list == -999.0] = 0
    wd_list[ws_list == -999.0] = 0
    mask = ws_list == 0
    
    # Se quitan los ceros, resultado de valores invalidos y se rellena 
    # ... con el valor válido más cercano.
    if rellenar_faltantes:
        lat_WS_f    = []
        lon_WS_f    = []
        flag_list_f = []
        ws_list_f   = []
        wd_list_f   = []
        for i in range(len(wd_list)):
            if not np.sum(mask[i]):
                lat_WS_f.append(lat_WS[i])
                lon_WS_f.append(lon_WS[i])
                flag_list_f.append(lon_WS[i])
                ws_list_f.append(ws_list[i])
                wd_list_f.append(wd_list[i])

        lat_WS = np.array(lat_WS_f)
        lon_WS = np.array(lon_WS_f)
        flag_list = np.array(flag_list_f)
        ws_list   = np.array(ws_list_f)
        wd_list   = np.array(wd_list_f)   

    # Pasamos primero de grados a radianes, tomando en cuenta que N=0°,E=90°
    wd_list = np.radians(360 - wd_list) 
    # Obtenemos las componentes del vector de dirección.
    ws_lat_list = -np.cos(wd_list)*ws_list
    ws_lon_list = np.sin(wd_list)*ws_list

    print("Promedio WS: ", np.mean(ws_list)) # --- > Métrica, promedio de la velocidad de viento.


    # PASO 2: Obtenemos el mesh de los datos, tomando como referencia el array del Optical Depth.

    LAT_WS_MESH , LON_WS_MESH = latlonArray(nc=nc_ref,enviar_0_0=False)

    # Reduccimos con la escala indicada.
    LON_WS_MESH = LON_WS_MESH[::reducción,::reducción]
    LAT_WS_MESH = LAT_WS_MESH[::reducción,::reducción]

    # PASO 3: Hacemos la asignación a cada punto.
    WS_lat  = np.zeros(LON_WS_MESH.shape)
    WS_lon  = np.zeros(LON_WS_MESH.shape)

    for i in range(LON_WS_MESH.shape[0]):
        for j in range(LON_WS_MESH.shape[1]):

            lat_from_grid = LAT_WS_MESH[i,j]
            lon_from_grid = LON_WS_MESH[i,j]

            dif_lat = lat_WS - lat_from_grid
            dif_lon = lon_WS - lon_from_grid

            distance = dif_lat**2 + dif_lon**2

            min_value_index = np.argmin(distance)
            min_distance    = distance[min_value_index]

            if min_distance < 1*dx:
                WS_lat[i,j] = ws_lat_list[min_value_index]
                WS_lon[i,j] = ws_lon_list[min_value_index]

    # Volvemos a escalar hacia arriba.
    WS_lat = scipy.ndimage.zoom(WS_lat,50,mode="nearest",order=0)
    WS_lon = scipy.ndimage.zoom(WS_lon,50,mode="nearest",order=0)
    
    # Aplico correción de signo a WS_lat , o se el motivo pero parec encajar mucho mejor
    # con las ímagenes satelitales con el negativo.
    return -WS_lat , WS_lon

# FUNCIONES PARA DESCARGA POR LOS AWS BUCKETS --------------------------

def _identificarBandas(df_files):
    """
    Le añade la información de a que banda pertence cada archivo, dado el nombre de un
    archivo netCDF diretamente descargado del los servidores usando regular expressions.
    """
    
    Bandas = []
    
    for line in df_files["file"]:
        file_name = str(line)
    
        # Obtenemos los indices donde se encuentra la información de la banda. -M6C%%_
        # Nota, solo nos interesa las imágenes del Scan Mode 3 o 6, siendo el modo 6 "M6" el modelo por default del satélite.

        match  = re.search(r"-M6C\d\d_",file_name)
        if match == None:
            match = re.search(r"-M3C\d\d_",file_name)
        span   = match.span()

        # Número de banda. (En string)
        banda = file_name[span[1]-3:span[1]-1]

        Bandas.append(int(banda))
    
    df_files["Banda"] = Bandas
    return df_files


def _goes_file_df(satellite, product, start, end, refresh=True):
    """
    Get list of requested GOES files as pandas.DataFrame.
    Parameters
    ----------
    satellite : str
    product : str
    start : datetime
    end : datetime
    refresh : bool
        Refresh the s3fs.S3FileSystem object when files are listed.
        Default True will refresh and not use a cached list.
    """
    fs = s3fs.S3FileSystem(anon=True)
    
    DATES = pd.date_range(f"{start:%Y-%m-%d %H:00}", f"{end:%Y-%m-%d %H:00}", freq="1H")

    # List all files for each date
    # ----------------------------
    files = []
    for DATE in DATES:
        files += fs.ls(f"{satellite}/{product}/{DATE:%Y/%j/%H/}", refresh=refresh)

    # Build a table of the files
    # --------------------------
    df = pd.DataFrame(files, columns=["file"])
    df[["start", "end", "creation"]] = (
        df["file"].str.rsplit("_", expand=True, n=3).loc[:, 1:]
    )

    # Filter files by requested time range
    # ------------------------------------
    # Convert filename datetime string to datetime object
    df["start"] = pd.to_datetime(df.start, format="s%Y%j%H%M%S%f")
    df["end"] = pd.to_datetime(df.end, format="e%Y%j%H%M%S%f")
    df["creation"] = pd.to_datetime(df.creation, format="c%Y%j%H%M%S%f.nc")

    # Filter by files within the requested time range
    df = df.loc[df.start >= start].loc[df.end <= end].reset_index(drop=True)

    return df


def descargaIntervaloGOES16(producto,
                            datetime_inicio,
                            datetime_final,
                            banda=None,
                            output_path="NETCDF_DATA/",
                            verbose=False):

    # Creamos el directorio si no existe.
    Path(output_path).mkdir(parents=True, exist_ok=True)
    
    # Nos conectamos a los servidores con credencial anónima. 
    fs = s3fs.S3FileSystem(anon=True)
    
    # Lista de productos
    lista_productos = fs.ls(f"noaa-goes16")

    # Asignamos fecha
    start = datetime_inicio
    end   = datetime_final

    # Obtenemos el dataframe con los elementos más recientes de cada banda.
    df = _goes_file_df(satellite="noaa-goes16",product=producto,start=start,end=end,refresh=True)

    
    # Identificamos cada archivo con la banda a la que corresponde.
    if banda != None:
        df = _identificarBandas(df) # Puse mas debug en la función.
        df = df[df["Banda"] == banda]

    descargados = 0
    a_descargar = len(df)

    # Descarga de los datos.
    for index in range(a_descargar):
        
        descarga_correcta = False

        file_name = df["file"].values[index]
        match  = re.search(r"OR_ABI.+",file_name)
        span   = match.span()
        output_name = file_name[span[0]:span[1]]

        # Si ya existe el archivo, continuamos.
        objeto_path = Path(output_path + output_name)
        if objeto_path.is_file():
            descargados += 1
            continue

        while descarga_correcta == False:
            try:
                fs.get(file_name, output_path + output_name,)
            except KeyboardInterrupt:
                raise
            except:
                print("Error en la descarga, volviendo a intentar.")
                time.sleep(5)
            else:
                descarga_correcta = True
                descargados += 1
        if verbose:
            print(f"Archivo descargado : \n{output_name}")
            print(f"Descargados {descargados} de {a_descargar}","\n")
    if verbose:
        print("Descargar completa.")



def datosActualesGOES16(producto,
                        banda=None,
                        output_name="GOES-descarga.nc"):
    """
    
    Descarga los datos más recientes de las categorias ingresadas, desde datos alojados en AWS.
    Los guarda en formato netCDF bajo el mismo nombre por los que se sobrescriben los datos.
    
    Cuando el producto es de clase ABI-L1b-RadC es necesario introducir la bada
    que se desea descargar.

    Basado en proyecto goes2go : https://github.com/blaylockbk/goes2go/
    
    LA FUNCIÓN SIGUE EN DESAROLLO, SOLO USAR CON PRODUCTOS EN EL DOMINIO DE CONUS.
    """
    
    # Nos conectamos a los servidores con credencial anónima. 
    fs = s3fs.S3FileSystem(anon=True)
    
    # Lista de productos
    lista_productos = fs.ls(f"noaa-goes16")
    
    # Revisamos si el producto solicitado está en la lista de productos disponibles.
    #assert(producto in lista_productos,f"El nombre del producto debe de ser {lista_productos}")
    
    # Obtenemos el intervalo de tiempo en el que buscaremos los archivos. (Hora UTC)
    start = datetime.utcnow() - timedelta(hours=1)
    end   = datetime.utcnow()
    

    # Obtenemos el dataframe con los elementos más recientes de cada banda.
    df = _goes_file_df(satellite="noaa-goes16",product=producto,start=start,end=end)
    df = df.loc[df.start == df.start.max()].reset_index(drop=True)

    # Identificamos cada archivo con la banda a la que corresponde.
    if banda != None:
        df = _identificarBandas(df)
        df = df[df["Banda"] == banda]
    
    #assert(len(df) > 0,"No se encontraron archivos.")
    if len(df) > 1 : 
        print("Aviso: Se encontró más de un archivo, solo se descargará el primero.")
        print(df,"\n")
        file_name = df["file"].values[0]
    else:
        # Obtenemos el nombre del archivo a descargar.
        file_name = df["file"].values[0]
    
    
    # Descarga de los datos.
    fs.get(file_name,output_name)
    print("Descargar completa.")


def estado_general(nc,variable):
    """
    Si el archivo netCDF tiene algún tipo de corrupción,
    se retorna False (archivo inválido), si no se detécta
    corrupción se marca como verdadero.

    Se revisan que los datos contengan al menos un valor que no sea
    fill_value.
    """
    fill_value = nc.variables[variable]._FillValue
    datos = np.array(nc.variables[variable])    
    if np.min(datos) == fill_value:
        archivo_valido = False
    else:
        archivo_valido = True
    return archivo_valido