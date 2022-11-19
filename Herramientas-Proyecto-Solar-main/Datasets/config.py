
# CONFIGURACIONES GENERALES
#--------------------------

DATOS_SOLARES = "WU" # "NSRDB" o "WU"
# --> Año de los datos que conformarán el dataset. (Solo disponibles 2018,2019,2020)
AÑO_DATOS = 2020 

# CONFIGURACIONES DE LA DESCARGA DE DATOS SATÉLITALES
#----------------------------------------------------

 # --> Días del año del que se descargarán los datos. (12 valor recomendado)
DÍAS   = 3           # 8
BANDAS = [11,13,16]  # Bandas disponibles: 1-16

# No meodificar estos
PRODUCTO = "ABI-L1b-RadC"
VARIABLE = "Rad"

# Horas  (e UTC) en las que se descargarán los datos. (12:00 UTC equivale a 7:00 am hora México.)
HORA_INICIO_UTC , MIN_INICIO_UTC = 15 , 00 #12 , 00
HORA_FINAL_UTC  , MIN_FINAL_UTC  = 20 , 00 #23 , 59

# CONFIGURACIÓN DE LA GENERACIÓN DE DATASETS
#-------------------------------------------:
RESOLUCIÓN      = 10#15   # --> Resolución del grid con el que se divirá méxico. (15 valor recomendado)
VENTANA_RECORTE = 10      # [km] --> Tamaño de la ventana de recoorte alrededor del punto en el pre-procesado.

# Si hay problemas con la memoria ram subir este numero por ejemplo a 10.
NUM_LOCALIDADES_EN_CHUNK = 5

# --> Límites geográficos para la generación del grid espacial.
INF_LAT , SUP_LAT =   16.8 ,  24.3
INF_LON , SUP_LON = -110.8 , -93.1
# ----------------------------------------------------------------------------------------------------

import os
import sys

_path_script    = os.path.realpath(__file__) 
_path_script    = "/".join(_path_script.split("/")[:-1])
sys.path.append(_path_script + "/../")

import h5py
import pickle
import datetime
import numpy  as np
import pandas as pd
from   pathlib import Path
import lib.f_generales as general

PATH_DESCARGA_GOES  = _path_script + "/Descargas/GOES/"
PATH_DESCARGA_NSRDB = _path_script + "/Descargas/NSRDB/"
PATH_DESCARGA_WU    = _path_script + "/Descargas/WU/"

PATH_PREPROCESADO_GOES = _path_script + "/Preprocesado_GOES/Temporal/"
PATH_DATASET_GOES      = _path_script + "/Preprocesado_GOES/"

PATH_CSV_ESTACIONES = _path_script + "/../Recursos/EstacionesMetereológicas_WU.csv"
PATH_MAPA_ELEVACIÓN = _path_script + "/../Recursos/Altura_CONUS_1500_2500.h5"
PATH_SHAPEFILE = _path_script + "/../Recursos/Shapefiles/shape_file.shp"
PATH_CONFIG    = _path_script + "/Config"
PATH_RECURSOS  = _path_script + "/../Recursos"

PATH_DATASET_FINAL = _path_script + "/Datasets/"

fill_value = {
    1:1023,
    2:4095,
    3:1023,
    4:2047,
    5:1023,
    6:1023,
    7:16383,
    8:4095,
    9:2047,
    10:4095,
    11:4095,
    12:2047,
    13:4095,
    14:4095,
    15:4095,
    16:1023
    }

resolución_bandas = {
    1:1,
    2:0.5,
    3:1,
    4:2,
    5:1,
    6:2,
    7:2,
    8:2,
    9:2,
    10:2,
    11:2,
    12:2,
    13:2,
    14:2,
    15:2,
    16:2,
}

# 0: bandas refectivas.
# 1: bandas emisivas.
clasificación_bandas = {
    1:0,
    2:0,
    3:0,
    4:0,
    5:0,
    6:0,
    7:1,
    8:1,
    9:1,
    10:1,
    11:1,
    12:1,
    13:1,
    14:1,
    15:1,
    16:1,
}

FLAGS_GOES = [2,3,4]


# AJUSTES DE LA CONFIGURACIÓN ----------------------------------------

def cargar_mask_espacial():
    """
    Cargamos el mask espacial dada la pre-configuración.
    """
    try:
        with open(_path_script + "/config.pickle","rb") as file:
            dic_config = pickle.load(file)
    except FileNotFoundError:
        mensaje = "Se requiere ejecutar primero el script config.py primero."
        raise FileNotFoundError(mensaje)

    Lat = dic_config["Lat"]
    Lon = dic_config["Lon"]

    return Lat , Lon
        

def cargar_mask_temporal(retornar_datetime:bool=False):
    """
    Cargamos el mask temporal dada la pre-configuración.
    """
    try:
        with open(_path_script + "/config.pickle","rb") as file:
            dic_config = pickle.load(file)
    except FileNotFoundError:
        mensaje = "Se requiere ejecutar primero el script config.py primero."
        raise FileNotFoundError(mensaje)
    
    días_descarga = dic_config["mask temporal"]

    # Si parámetro retornar_datetime.
    if retornar_datetime:
        días_descarga_datetime = []
        for día in días_descarga:
            primer_día_año = datetime.datetime(AÑO_DATOS,1,1,0,0)
            delta_días     = datetime.timedelta(days=int(día))
            fecha          = primer_día_año + delta_días
            días_descarga_datetime.append(fecha)
        return días_descarga_datetime
    else:
        return días_descarga

def guardar_batch(datos_array,datos_DQF,datos_t,datos_coordenadas,banda,nombre_batch,path):
    "Guarda un batch de datos al disco."
    path_output_dataset = f"{path}{banda}/"
    Path(path_output_dataset).mkdir(parents=True,exist_ok=True)

    with h5py.File(f"{path_output_dataset}{nombre_batch}", "w") as file:
        # Ajustamos los arrays.
        res = VENTANA_RECORTE
        datos_array = np.array(datos_array) #.reshape(-1,res,res).astype(np.uint16)
        datos_DQF   = np.array(datos_DQF  ) #.reshape(-1,res,res).astype(np.uint16)
        datos_t     = np.array(datos_t) #.astype(np.uint32)
        datos_coordenadas = np.array(datos_coordenadas)
        file.create_dataset("T"    ,data=datos_t    )
        file.create_dataset("Datos",data=datos_array)
        file.create_dataset("DQF"  ,data=datos_DQF  )
        Lat = datos_coordenadas[0]
        Lon = datos_coordenadas[1]
        datos_coordenadas = np.stack([Lat,Lon],axis=1)
        file.create_dataset("Coordenadas",data=datos_coordenadas)



if __name__ == "__main__":
    
    print("")
    print("----------------------------")
    print("SCRIPT DE PRE-CONFIGURACIÓN ")
    print("----------------------------\n")


    # Generamos el mask espacial de los datos.
    print("Generando el mask espacial ...")

    if DATOS_SOLARES == "NSRDB":
        Lon , Lat , Mask_espacial = general.generar_mask_espacial(
            INF_LAT=INF_LAT,
            SUP_LAT=SUP_LAT,
            INF_LON=INF_LON,
            SUP_LON=SUP_LON,
            RESOLUCIÓN=RESOLUCIÓN,
            PATH_SHAPEFILE=PATH_SHAPEFILE,
        )
        lista_lat , lista_lon  = [] , []
        for i in range(RESOLUCIÓN):
            for j in range(RESOLUCIÓN):
                lat , lon = Lat[i,j] , Lon[i,j]
                if Mask_espacial[i,j]:
                    lista_lat.append(lat)
                    lista_lon.append(lon)
    
    elif DATOS_SOLARES == "WU":
        df_WU = pd.read_csv(PATH_CSV_ESTACIONES)
        lista_lat , lista_lon = list(df_WU["Latitud"].values) , list(df_WU["Longitud"].values)
    
    else:
        raise ValueError("No se ha puesto un nombre de \"DATOS_SOLARES\" valido.\nOpciones válidas: \"NSRDB\",\"WU\"")


    # Generamos el mask temporal de los datos
    print("Generando el mask temporal...")

    Mask_temporal = general.generar_dias_año(dias=DÍAS)
    
    # Guardamos los objetos generados por la configuración.
    print("Guardando la configuración...")

    dic_config = {
        "Lat"  : lista_lat ,
        "Lon"  : lista_lon ,
        "mask temporal" : Mask_temporal,
    }

    with open( _path_script + "/config.pickle","wb") as file:
        pickle.dump(dic_config,file)

    print("Script de pre-configuración terminado!")
