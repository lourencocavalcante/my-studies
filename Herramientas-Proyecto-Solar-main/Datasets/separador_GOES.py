import os
import sys
_path_script    = os.path.realpath(__file__) 
_path_script    = "/".join(_path_script.split("/")[:-1])
sys.path.append(_path_script + "/../")

import time
import netCDF4
import h5py
import shutil
import lib.f_generales as general
import numpy  as np
import pandas as pd
import lib.libGOES as GOES
from   pathlib import Path

import config

# Cargando configuraciones.
Lat,Lon       = config.cargar_mask_espacial()
días_descarga = config.cargar_mask_temporal()

batch_totales   = len(días_descarga)
num_comunidades = len(Lat)

# Obtenemos las latitudes y Longitudes
Lat , Lon         = np.array(Lat) , np.array(Lon)
coordenadas_mask  = np.stack([Lat,Lon],axis=1)

class Chunk:
    def __init__(self,lista_index,lista_lat,lista_lon,banda):
        self.banda = banda
        self.lista_lat = lista_lat
        self.lista_lon = lista_lon
        self.lista_index = lista_index
        self.num_localidades   = len(self.lista_lat)
        self.datos_localidades = [{} for _ in range(self.num_localidades)]

        # Checks
        if len(self.lista_lon) != self.num_localidades:
            raise IndexError("Listas de entrada no son del mismo tamaño.")
        if len(self.lista_index) != self.num_localidades:
            raise IndexError("Listas de entrada no son del mismo tamaño.")
        
    def recopilar_datos(self):
        # Encontramos cuantos batches hay de la banda
        batch_totales = len(días_descarga)
        # Escaneamos batch
        for num_batch in range(batch_totales):
            path_batch = f"{config.PATH_PREPROCESADO_GOES}{self.banda}/" + "Batch_" + str(num_batch).zfill(2) + ".h5"
            with h5py.File(path_batch,"r") as batch:
                Arrays = batch["Datos"][()]
                DQF    = batch["DQF"][()]
                T      = batch["T"][()]
                Coordenadas = batch["Coordenadas"][()]
            
            # Iteramos sobre cada comunidad
            for i in range(self.num_localidades):
                lat = self.lista_lat[i]
                lon = self.lista_lon[i]
                indice_localidad = self.lista_index[i]

                # valores de cada localidad.
                array = Arrays[indice_localidad::num_comunidades]
                dqf   = DQF[indice_localidad::num_comunidades]
                t     = T[indice_localidad::num_comunidades]
                coordenadas = Coordenadas[indice_localidad::num_comunidades]

                # Revisamos que todo coincida.
                if np.sum(coordenadas[:,0] != lat) > 0:
                    raise ValueError(f"coordenada de latitud no coincide {lat}: \n{coordenadas[:,0]}")
                if np.sum(coordenadas[:,1] != lon) > 0:
                    raise ValueError(f"coordenada de longitud no coincide {lon}: \n{coordenadas[:,1]}")

                # Juntamos todo.    
                try:
                    self.datos_localidades[i]["Coordenadas"] += list(coordenadas)
                    self.datos_localidades[i]["Datos"] += list(array)
                    self.datos_localidades[i]["DQF"]   += list(dqf)
                    self.datos_localidades[i]["t"]     += list(t)
                except KeyError:
                    self.datos_localidades[i]["Coordenadas"] = list(coordenadas)
                    self.datos_localidades[i]["Datos"] = list(array)
                    self.datos_localidades[i]["DQF"]   = list(dqf)
                    self.datos_localidades[i]["t"]     = list(t)
        
        # Guardamos localidad.
        for i in range(self.num_localidades):
            lat, lon = self.datos_localidades[i]["Coordenadas"][0]
            nombre_archivo = general.asignarNombreArchivo(lat=lat,lon=lon,extensión="h5")
            config.guardar_batch(
                datos_array = self.datos_localidades[i]["Datos"],
                datos_DQF   = self.datos_localidades[i]["DQF"]  ,
                datos_t     =  self.datos_localidades[i]["t"]   ,
                datos_coordenadas = self.datos_localidades[i]["Coordenadas"] ,
                banda = self.banda              ,
                nombre_batch = nombre_archivo   ,
                path = config.PATH_DATASET_GOES ,
            )

def separador_GOES(banda):
    print(f"Iniciando separación para banda {banda}...")
    lista_index_localidades       = np.array_split(np.arange(num_comunidades),config.NUM_LOCALIDADES_EN_CHUNK)
    lista_coordenadas_localidades = np.array_split(coordenadas_mask,config.NUM_LOCALIDADES_EN_CHUNK)
    chunks_procesados  = 0
    tiempo_o = time.time()
    for num_chunk in range(config.NUM_LOCALIDADES_EN_CHUNK):
        index_localidades = lista_index_localidades[num_chunk]
        coordenadas       = lista_coordenadas_localidades[num_chunk]
        lista_lat , lista_lon = coordenadas[:,0] , coordenadas[:,1]
        chunk = Chunk(index_localidades,lista_lat,lista_lon,banda=banda)
        chunk.recopilar_datos()

        chunks_procesados += 1
        print(f"Chunks procesados {chunks_procesados} de {config.NUM_LOCALIDADES_EN_CHUNK}")
        t = time.time()
        t = round((t-tiempo_o)/60 , 2)
        print(f"Tiempo transcurrido {t} min\n")

if __name__ == "__main__":
    texto = """
-----------------------------------------
SCRIPT DE SEPARACIÓN DE DATOS SATÉLITALES
-----------------------------------------
"""
    print(texto)
    for banda in config.BANDAS:
        separador_GOES(banda)
    print("Script de separación finalizado!")