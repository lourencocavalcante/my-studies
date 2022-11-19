
# CONFIGURACIONES
# ---------------

# Datos satélitales que conformarán el dataset final.
BANDAS  = [13,14] # --> Bandas que conformarán el dataset.

# Configuración de sincronización
LONGITUD_SECUENCIA    = 4  
UMBRAL_SINCRONIZACIÓN = 4  # minutos (recomendado 2).
UMBRAL_SERIE          = 7  # minutos (recomendado 7), se ignora si LONGITUD_SECUENCIA = 1. 

# Escalado: Todos las bandas se escalan a un mismo tamaño.
# (Facilita el manejo de bandas con resoluciones diferentes sin embargo el dataset final tendrá un mayor tamaño.)
ESCALAR = False

# Guarda el datset final completo en un único archivo.
UNIR_BATCHES = True

# -------------------------------------------------------------------

import os
import sys
_path_script    = os.path.realpath(__file__) 
_path_script    = "/".join(_path_script.split("/")[:-1])
sys.path.append(_path_script + "/../")

import h5py
import config
import datetime
import scipy.ndimage
import numpy  as np
import pandas as pd 
import lib.libGOES as goes
import lib.libSinc as Sinc
import lib.f_generales as general

from   pathlib import Path

# Abrimos el archivo de pre-configuración.
print("Cargando archivo de configuración...")
días_descarga = config.cargar_mask_temporal()
Lat,Lon       = config.cargar_mask_espacial()
Path(config.PATH_DATASET_FINAL).mkdir(parents=True,exist_ok=True)

# Revisamos que las bandas puestas estén descargada.
print("Revisando la existencia de todos los archivos a usar...")
for num_banda in BANDAS:
    if os.path.exists(config.PATH_DATASET_GOES + f"{num_banda}/") == False: raise FileNotFoundError(f"No se encontro el dataset de la banda {num_banda}")

def nombre_dataset():
    nombre = ""
    nombre += f"Ventana_{config.VENTANA_RECORTE}-"
    nombre += f"Bandas_"
    for banda in BANDAS:
        nombre += f"{banda}_"
    nombre += f"-Secuencia_{LONGITUD_SECUENCIA}-"
    nombre += f"Resolucion_{config.RESOLUCIÓN}-{config.DATOS_SOLARES}"
    return nombre + ".h5"

# Definimos los callbacks para obtener la lista de datetime.
def datetime_bandas(T):
    "Obtenemos lista de objetos datetime de las bandas."
    lista_datetime = [goes.obtenerFecha_GOES(int(t),return_datetime=True) for t in T]
    return lista_datetime


# Scritpt de procesado de batch
def procesar_batch(lat,lon):
    # Generamos el nombre de guardado.
    nombre_batch = general.asignarNombreArchivo(lat=lat,lon=lon,extensión="")
    # Generamos un dato con temporalidad por cada banda.
    datos_temporales = []
    for banda in BANDAS:
        # Abrimos batch.
        with h5py.File(config.PATH_DATASET_GOES + f"{banda}/"+ nombre_batch+ "h5","r") as batch:
            Arrays = batch["Datos"][()]
            DQF    = batch["DQF"][()]
            T      = batch["T"][()]
        # Escalamos batch
        if ESCALAR:
            escalado = config.resolución_bandas[banda]*2
            if escalado != 1:
                Arrays = scipy.ndimage.zoom(Arrays,escalado,order=0,mode="nearest")
                DQF    = scipy.ndimage.zoom(DQF,escalado,order=0,mode="nearest")
        
        # Transformaos a datetime la lista de tiempo UNIX.
        lista_datetime = datetime_bandas(T)
        Datos = np.stack([Arrays,DQF],axis=1)
        Datos = list(Datos)
        datos_temporales.append(Sinc.DatosTemporales(lista_datos=Datos,lista_datetime=lista_datetime))

    # Iniciamos sincronización
    sincronizador = Sinc.Sincronizador(datos_temporales,verbose=True)
    serie_tiempo  = sincronizador.generarSerieTiempo(UMBRAL_SINCRONIZACIÓN*60,UMBRAL_SERIE*60,longitud=LONGITUD_SECUENCIA)
    serie_tiempo  = np.array(serie_tiempo)
    num_series    = serie_tiempo.shape[0]

    # Obtenemos los datos asociados a las bandas.
    datos_GOES = {}

    try:

        for i,banda in zip(range(len(BANDAS)),BANDAS):
            lista_datos_serie = []
            for j in range(LONGITUD_SECUENCIA):
                dato = np.take(np.array(datos_temporales[i].lista_datos),serie_tiempo[:,j,i],axis=0) # Donde j es el índice delmomento en la serie y i es el índice del tipo de dato a extraer.

                # Expandimos dimenciones para mantener como primer índice al index de la serie de tiempo.
                dato = np.expand_dims(dato,axis=1)
                lista_datos_serie.append(dato)
            
            datos_GOES[str(banda)] = np.concatenate(lista_datos_serie,axis=1) # --> datos_GOES[str(banda)][indice_serie][indice_momento][0:array 1:DQF][x][y]
    
    except IndexError as err:
        mensaje_error = f"""
"Error en la extración de datos de la serie de tiempo:

Shape serie_tiempo: {np.array(serie_tiempo).shape}

* Una causa puede ser un umbral de sincronizacion muy por abajo. Se recomienda
  aumentar el umbral.

* Si no funciona lo anterior otra causa puede ser el haber cambiado recientemente 
  la configuración  y esta ya no es compatible con los archivos preprocesados. 
  Probar en borrar la carpeta de archivos descargados y pre-procesados.

""" 
        raise IndexError(mensaje_error)

    # Revisamos datos inválidos de cada uno de los datos de todos los momentos en las series.
    indices_validos  = []
    for i in range(num_series): # Iteramos sobre la lista de series de tiempo.
        puntos_invalidos = 0
        for banda in BANDAS:
            for j in range(LONGITUD_SECUENCIA):
                # Sumamos los puntos con algún flag
                for flag in config.FLAGS_GOES:
                    puntos_invalidos += np.sum(datos_GOES[str(banda)][i,j,1,:,:] == flag)
                # Sumamos los puntos que tengan fill values.
                puntos_invalidos += np.sum(datos_GOES[str(banda)][i,j,0,:,:] == config.fill_value[banda])

        # Si toda una serie de tiempo no tiene puntos inválidos, se agrega a la lista de índices válidos. 
        if puntos_invalidos == 0:
            indices_validos.append(i)
    
    # Extraemos datos válidos.
    for banda in BANDAS:
        datos = datos_GOES[str(banda)][:,:,0,:,:] # Le quitamos el array de DQF en los datos.
        datos = datos[indices_validos,:,:,:]
        datos_GOES[str(banda)] = datos

    return datos_GOES

if __name__ == "__main__":
    texto = f"""
--------------------------------
SCRIPT DE GENERACIÓN DE DATASETS
--------------------------------

    Configuración:

    * Bandas : {BANDAS}
    * Ventana: {config.VENTANA_RECORTE}
    * Longitud Serie de Tiempo: {LONGITUD_SECUENCIA}
    * Umbral Sincronización   : {UMBRAL_SINCRONIZACIÓN}

------------------------------------
"""
    print(texto)

    continuar = input("Continuar ? [y/n]")
    if continuar != "y": sys.exit()

    num_batch_procesados = 0
    num_batch_totales    = len(Lat)

    # diccionarios para concatenar datos
    datos_GOES = {}
    for banda in BANDAS:
        datos_GOES[str(banda)] = []
    
    # Obtenemos el nombre del batch (sin la extención).
    for i in range(len(Lat)):
        lat , lon = Lat[i],Lon[i]
        try:
            batch_datos_GOES  = procesar_batch(lat,lon)
        except IndexError as err:
            print(f"Durante el procesamiento del batch en {lat} {lon} ha ocurrido el siguiente error:\n{err}")
        else:
            if UNIR_BATCHES:
                # Juntamos todo en un diccionario.
                for banda in BANDAS:
                    datos_GOES[str(banda)].append(batch_datos_GOES[str(banda)])

            else:
                raise NotImplementedError("Aun no implemento el caso de no unir batches.")
        finally:
            num_batch_procesados += 1
            print(f"Batch procesados {num_batch_procesados} de {int(num_batch_totales)}, progreso {round(100*num_batch_procesados/num_batch_totales,1)}%")
    
    # Concatenamos y guardamos.
    print("\nGuardando datos...")
    nombre_dataset_final =  config.PATH_DATASET_FINAL +  nombre_dataset()
    with h5py.File(nombre_dataset_final,"w") as dataset:
        for banda in BANDAS:
            datos_GOES[str(banda)] = np.concatenate(datos_GOES[str(banda)],axis=0) # Concatenamos en el axis del índice momento.
            dataset.create_dataset(name=str(banda),data=datos_GOES[str(banda)],dtype=np.float32)


    print(f"Se ha creado el dataset {nombre_dataset()} con {datos_GOES[str(banda)].shape[0]} series de tiempo!" )
    print("Script de generación de dataset terminado!")





