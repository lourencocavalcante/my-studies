"""
Web-scraping de los datos de weather underground.
"""

import os
import sys
_path_script    = os.path.realpath(__file__) 
_path_script    = "/".join(_path_script.split("/")[:-1])
sys.path.append(_path_script + "/../")

import pathlib
import config
import pandas as pd
import lib.libWU       as WU
import lib.f_generales as general

# Revisamos la existencia de los paths.
pathlib.Path(config.PATH_DESCARGA_WU).mkdir(parents=True,exist_ok=True)

# Cargamos la configurción de los días a descargar.
días_descarga = config.cargar_mask_temporal(retornar_datetime=False)

# Cargamos las estaciones metereológicas.
df_estaciones = pd.read_csv(config.PATH_CSV_ESTACIONES)

print("Iniciando descarga de los datos de Weather Underground...")
for index,localidad in df_estaciones.iterrows():

    # Obtenemos los datos de la estación.
    nombre_estación = localidad["Estación"]
    latitud  = localidad["Latitud" ]
    longitud = localidad["Longitud"]

    print(f"Descargando datos de {nombre_estación}...")
    df = WU.descarga_lugar(estación=nombre_estación,año=config.AÑO_DATOS,latitud=latitud,longitud=longitud,lista_num_dias=días_descarga)

    nombre_guardado = general.asignarNombreArchivo(lat=latitud,lon=longitud,extensión="csv")
    df.to_csv(f"{config.PATH_DESCARGA_WU}{nombre_guardado}" )

print("Script de descarga de los datos de Weather Underground completada!")



