import os
import sys
_path_script    = os.path.realpath(__file__) 
_path_script    = "/".join(_path_script.split("/")[:-1])
sys.path.append(_path_script + "/../")

import time
import netCDF4
import numpy  as np
import lib.libGOES as GOES
from   pathlib import Path

import config
import lib.f_generales as general

# Cargamos la configuración.
dias_descarga = config.cargar_mask_temporal()

def descarga_banda_GOES(banda):
    path_descarga = f"{config.PATH_DESCARGA_GOES}{banda}/"

    dias_a_descargar = len(dias_descarga)
    dias_descargados = 0
    tiempo_o = time.time()

    for i,día_del_año in zip(range(len(dias_descarga)),dias_descarga):
            # Creamos los directorios de salida de descarga.
            path_batch = path_descarga +  "Batch_" + str(i).zfill(2) +"/"
            Path(path_batch).mkdir(parents=True,exist_ok=True)
            # Obtenemos los objetos datetime, del inicio y final.
            inicio,final = general.obtenerIntervaloUTC(
                int(día_del_año) ,
                config.HORA_INICIO_UTC  ,
                config.MIN_INICIO_UTC   ,
                config.HORA_FINAL_UTC   ,
                config.MIN_FINAL_UTC    )       
            # Descargamos los datos satélitales.
            try:
                GOES.descargaIntervaloGOES16(
                    producto        = config.PRODUCTO    ,
                    datetime_inicio = inicio      ,
                    datetime_final  = final       ,
                    banda       = banda           ,
                    output_path = path_batch      )
            except AttributeError as err:
                print("No se encontraron datos bajo el Scan Mode 3 o 6 del satélite. Omitiendo descarga...\n")
            
            # Métricas.
            tiempo = time.time()
            tiempo_transcurrido = round(( tiempo - tiempo_o ) / 60,1)
            dias_descargados += 1
            print(f"Días descargados {dias_descargados} de {dias_a_descargar} en {tiempo_transcurrido} min")
            print("Revisando integridad general de los archivos descargados...")
            lista_descarga = os.listdir(path_batch)
            lista_descarga.sort()
            for archivo in lista_descarga:
                # Abrimos archivo.
                try:
                    nc = netCDF4.Dataset(path_batch + archivo)
                    # Revisando estado general.
                    archivo_valido = GOES.estado_general(nc,config.VARIABLE)
                    if archivo_valido  == False:
                        print("Archivo netCDF corrupto, eliminando.")
                        os.remove(path_batch + archivo)
                    # Revisando estado de la fecha.
                    try:
                        t = float(np.array(nc.variables["t"]))
                    except:
                        t = float(np.array(nc.variables["time"])[0])
                    fecha = GOES.obtenerFecha_GOES(nc,return_datetime=True)
                    # Revisamos que el año de los datos coincidan.
                    if fecha.year != config.AÑO_DATOS:
                        print("Fecha en el archivo netCDF corrupto,eliminando.")
                        os.remove(path_batch + archivo)
                    nc.close()
                except FileNotFoundError: 
                    raise FileNotFoundError("No se encontró archivo .nc")
                except:
                    print("Error al abrir archivo netCDF.")
                    continue
            print("")

    print(f"Descarga de datos finalizada de la banda {banda}!")

if __name__ == "__main__":
    print("\nSCRIPT DE DESCARGA DE DATOS SATELITALES \n")

    texto = f"""
    Revisar la información de los datos a descargar:
    ------------------------------------------------
    Producto : {config.PRODUCTO}
    Banda    : {config.BANDAS}
    Variable : {config.VARIABLE}

    Días a descargar : {config.DÍAS}
    Hora inicio : {config.HORA_INICIO_UTC}:{config.MIN_INICIO_UTC}
    Hora final  : {config.HORA_FINAL_UTC}:{config.MIN_FINAL_UTC}
    ------------------------------------------------
    """
    print(texto)

    continuar = input("Continuar? [y/n]: ")
    if continuar != "y":
        sys.exit()
    
    for banda in config.BANDAS:
        print(f"\nIniciando descarga de datos de banda {banda}...\n")
        descarga_banda_GOES(banda)
        print("Script de descarga finalizado!")