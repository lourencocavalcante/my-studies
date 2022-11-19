import os
import sys
_path_script    = os.path.realpath(__file__) 
_path_script    = "/".join(_path_script.split("/")[:-1])
sys.path.append(_path_script + "/../")

import re
import time
import h5py
import netCDF4
import datetime
import requests
import numpy  as np
import pandas as pd


from pathlib  import Path
from bs4      import BeautifulSoup as BS

import lib.libGOES     as GOES
from pvlib.location import Location

def obtenerDatos_WU(estación,día,mes,año,latitud,longitud,altura=None):
    """
    Realiza Webscrapping a la página de Weather underground.
    
    Parámetros
        - estación: Nombre de la estación dentro de la página de Weather Underground.
        - altura  : Si se deja en None se usará la altura con un mapa de alturas de 2Km de resolución.
    """

    # Obtenemos el html
    día = str(día)
    mes = str(mes).zfill(2)
    url = f"https://www.wunderground.com/dashboard/pws/{estación}/table/{año}-{mes}-{día}/{año}-{mes}-{día}/daily"
    html  = requests.get(url).text
    soup  = BS(html,"lxml")

    # Adquiramos la tabla en formato ¿¿ JSON ??
    tabla    = soup.find_all("script")[9]
    json_txt = re.findall(">.+",str(tabla))[0][1:-9]

    # Obtenemos Solar Radiation High
    GHI = re.findall("solarRadiationHigh&q;:[0-9]+\.*[0-9]*",json_txt)
    GHI = [float(valor[22:]) for valor in GHI]

    # Obtenemos el indice de radiación UV
    UV = re.findall("uvHigh&q;:[0-9]+\.*[0-9]*",json_txt)
    UV = [float(valor[10:]) for valor in UV]

    # Obtenemos el time-stamp
    T = re.findall("obsTimeUtc&q;:&q;[0-9-:T]+",json_txt)
    T = [t[17:] for t in T]

    # Algunas veces hay un dato extra de tiempo.
    if len(T) != len(GHI):
        T = T[:-1]
    
    # Revisamos que las longitudes coincidan.
    if len(T) != len(GHI) or len(T) != len(UV):
        raise ValueError(f"No coincide longitudes T:{len(T)} GHI:{len(GHI)} UV:{len(UV)}\nURL: {url}")
    
    if len(T) == 0:
        raise ValueError(f"No hay datos por descargar en este día.\nURL: {url}")

    # Pasamos los datos a datetime.
    T = [datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S") for t in T]
    Times = pd.DatetimeIndex(T)

    # Generamos las columnas de tiempo.
    Year   = [t.year   for t in T]
    Month  = [t.month  for t in T]
    Day    = [t.day    for t in T]
    Hour   = [t.hour   for t in T]
    Minute = [t.minute for t in T]

    # Obtenemos las columnas de Clearsky GHI and Solar zenit angle (librería pvlib).
    if altura == None:
        path_altura = _path_script + "/../Recursos/altura_CONUS_1500_2500.h5"
        path_nc     = _path_script + "/../Recursos/Banda13_Prueba.nc"
        nc = netCDF4.Dataset(path_nc)
        X = np.array(nc.variables["x"])
        Y = np.array(nc.variables["y"])
        lambda_o = nc.variables["goes_imager_projection"].longitude_of_projection_origin
        nc.close()
        nc = (X,Y,lambda_o)
        with h5py.File(path_altura,"r") as datos_altura:
            array_altura = datos_altura["Altura"][()]
            px_x , px_y  = GOES.coordinates2px_GOES(nc,latitud=latitud,longitud=longitud)
            altura = array_altura[px_y,px_x]
    
    pvlib_posición = Location(latitude=latitud,longitude=longitud,name=estación,tz="UTC",altitude=altura)
    df_clearsky    = pvlib_posición.get_clearsky(Times)
    df_position    = pvlib_posición.get_solarposition(Times)

    Clearsky_GHI = df_clearsky["ghi"]
    Clearsky_DNI = df_clearsky["dni"]
    Clearsky_DHI = df_clearsky["dni"]
    Zenith       = df_position["zenith"]

    # Devolvemos el dataframe.
    dic_df = {
        "Year"  :Year,
        "Month" :Month,
        "Day"   :Day,
        "Hour"  :Hour,
        "Minute":Minute,
        "GHI"   :GHI,
        "UV"    :UV,
        "Clearsky GHI":Clearsky_GHI,
        "Clearsky DNI":Clearsky_DNI,
        "Clearsky DHI":Clearsky_DHI,
        "Solar Zenith Angle":Zenith,
        }
    df = pd.DataFrame(dic_df).iloc[:-2]
    return df


def descarga_lugar(estación,año,lista_num_dias,latitud,longitud,altura=None):

    columnas = ["Year","Month","Day","Hour","Minute","GHI","UV","Clearsky GHI","Clearsky DNI","ClearSky DHI","Solar Zenith Angle"]
    df_dataset = pd.DataFrame(columns=columnas)

    for num_dia in lista_num_dias:
        # Obtenemos los parámetros de la fecha.
        enero_1 = datetime.datetime(año,1,1,0,0)
        fecha   = enero_1 + datetime.timedelta(days=int(num_dia))
        mes = fecha.month
        día = fecha.day
        # Descargamos datos.
        try:
            df_día = obtenerDatos_WU(estación=estación,año=año,mes=mes,día=día,latitud=latitud,longitud=longitud,altura=altura)
        except KeyboardInterrupt:
            raise
        except ValueError as err:
            print(f"Ha ocurrido el siguiente error en la descarga de los datos de la fecha {día}/{mes}/{año}: \n{err}")
            continue
        except:
            print("Ocurrio un error inesperado, saltando...")
            continue

        # Concatenamos
        df_dataset  = pd.concat([df_dataset,df_día],ignore_index=True)
    
    return df_dataset

    


    
    