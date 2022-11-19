"""
Adrián Ramírez

Scipt que descarga los datos de radiación solar de los puntos configurados.
"""
import os
import sys
_path_script    = os.path.realpath(__file__) 
_path_script    = "/".join(_path_script.split("/")[:-1])
sys.path.append(_path_script + "/../")

PATH_DESCARGA_NSRDB  = f"{_path_script}/Descargas/NSRDB/"

import config
import numpy as np
import lib.libNSRDB as NSRDB
import lib.f_generales as general

from pathlib import Path

# Nos aseguramos de crear el directorio de descarga.
Path(PATH_DESCARGA_NSRDB).mkdir(parents=True, exist_ok=True)

print(f"""
--------------------------------------
SCRIPT DE DESCARGA DE DATOS DEL NSRDB
--------------------------------------

CONFIGURACIÓN:

* Resolución    : {config.RESOLUCIÓN}
* Años descarga : {config.AÑO_DATOS}

--------------------------------------

""")

# Cargamos los datos de la configuración
print("Cargando archivo de configuración...")
Lat, Lon = config.cargar_mask_espacial()

por_descargar = len(Lat)
descargados   = 0

print("Iniciando descarga de los datos...")
for i in range(por_descargar):
    lat , lon = Lat[i] , Lon[i]
    # Asignamos un nombre al archivo.
    nombre_archivo_guardado = general.asignarNombreArchivo(lat=lat,lon=lon)
    # Si el archivo ya está descargado, saltamos.
    if Path(PATH_DESCARGA_NSRDB + nombre_archivo_guardado).is_file():
        descargados += 1
        continue
    # Bucle de descarga...
    descarga_correcta = False
    while descarga_correcta == False:
        try:
            df_data = NSRDB.getData(lat=lat,lon=lon,year=config.AÑO_DATOS,intervalo=5,UTC=True)
        except KeyboardInterrupt:
            raise
        except:
            print("Hubo un error en la descarga, repitiendo.")
        else:
            df_data.to_csv(PATH_DESCARGA_NSRDB + nombre_archivo_guardado)
            descargados += 1
            descarga_correcta = True
            print(f"Descargados {descargados} de {por_descargar}")

print("Descarga finalizada!")
