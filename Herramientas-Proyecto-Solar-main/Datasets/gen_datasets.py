"""
README

Script de combinación de datasets.

El objetivo de este  script es combinar las  diferentes fuentes 
de  datos (datos satélitales y datos  de radiación solar)  para
generar un único dataset con toda la información. Esto se logra
emparejando  cada dato de todas las fuentes de datos de acuerdo 
a la fecha  y hora  de cada uno deesos datos. Además se realiza
un procesado final a los datos.

IMPORTANTE!

* Es necesario haber ejecutado los scripts de "descarga_GOES.py"
  y "descarga_NSRDB.py".
"""

# CONFIGURACIONES
# ---------------

# Datos satélitales que conformarán el dataset final.
BANDAS  = [11,13,16] # --> Bandas que conformarán el dataset.

# Configuración de sincronización
LONGITUD_SECUENCIA    = 1  
UMBRAL_SINCRONIZACIÓN = 4  # minutos (recomendado 2).
UMBRAL_SERIE          = 7  # minutos (recomendado 7), se ignora si LONGITUD_SECUENCIA = 1. 

# Datos que se tomarán del NSRDB.
DATOS_SOLARES = ["Year","Month","Day","Hour","Minute","GHI","Solar Zenith Angle","Clearsky GHI","UV"]

# Configuración de la variable objetivo
DATO_OBJETIVO = "GHI"


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

if config.DATOS_SOLARES == "NSRDB":
    PATH_DATOS_SOLARES = config.PATH_DESCARGA_NSRDB
elif config.DATOS_SOLARES == "WU":
    PATH_DATOS_SOLARES = config.PATH_DESCARGA_WU
else:
    raise ValueError("No se ha puesto un nombre de \"DATOS_SOLARES\" valido.\nOpciones válidas: \"NSRDB\",\"WU\"")

# Añadimos columnas de coordendas!!
DATOS_SOLARES.append("Latitud")
DATOS_SOLARES.append("Longitud")

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

def datetime_datos_Solares(df):
    "Obtenemos lista de objetos datetime de los datos solares."
    año = df["Year"].values
    mes = df["Month"].values
    dia = df["Day"].values
    hora = df["Hour"].values
    minu = df["Minute"].values
    lista_datetime = [datetime.datetime(año[i],mes[i],dia[i],hora[i],minu[i]) for i  in range(len(año))]
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

    # Le añadimos el dato temporal de los datos de NSRDB.
    df = pd.read_csv(PATH_DATOS_SOLARES + nombre_batch + "csv")

    # Operaciones sobre el dataframe.
    Latitud  = np.ones(shape=(len(df),))*lat
    Longitud = np.ones(shape=(len(df),))*lon
    df["Latitud"]  = Latitud
    df["Longitud"] = Longitud
    
    lista_datetime = datetime_datos_Solares(df)
    try:
        datos_temporales.append(Sinc.DatosTemporales(lista_datos=df,lista_datetime=lista_datetime))
    except ValueError as err:
        print(f"Batch con el error: {lat},{lon}")
        raise
        

    # Iniciamos sincronización
    sincronizador = Sinc.Sincronizador(datos_temporales,verbose=True)
    serie_tiempo  = sincronizador.generarSerieTiempo(UMBRAL_SINCRONIZACIÓN*60,UMBRAL_SERIE*60,longitud=LONGITUD_SECUENCIA)
    serie_tiempo  = np.array(serie_tiempo)
    num_series    = serie_tiempo.shape[0]

    # Obtenemos los datos asociados a las bandas.
    datos_GOES = {}
    try:
        for i,banda in zip(range(len(BANDAS)),BANDAS):
            datos_GOES[str(banda)] = np.take(np.array(datos_temporales[i].lista_datos),serie_tiempo[:,i],axis=0)
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

    # Obtenemos los datos asociados a NSRDB
    datos_SOLARES = {} 
    for columna in DATOS_SOLARES:
        datos_SOLARES[columna] = df[columna].iloc[serie_tiempo[:,-1]].values

    # Revisamos datos inválidos.
    indices_validos  = []
    for i in range(datos_GOES[str(BANDAS[0])].shape[0]):
        puntos_invalidos = 0
        for banda in BANDAS:
            for flag in config.FLAGS_GOES:
                puntos_invalidos += np.sum(datos_GOES[str(banda)][i,1,:,:] == flag)
            # Sumamos los que tengan fill values.
            puntos_invalidos += np.sum(datos_GOES[str(banda)][i,0,:,:] == config.fill_value[banda])
        if puntos_invalidos == 0:
            indices_validos.append(i)
    
    # Extraemos datos válidos.
    for banda in BANDAS:
        datos = datos_GOES[str(banda)][:,0,:,:]
        datos = datos[indices_validos,:,:]
        datos_GOES[str(banda)] = datos
    for columna in DATOS_SOLARES:
        datos_SOLARES[columna] = datos_SOLARES[columna][indices_validos]
    
    return datos_GOES,datos_SOLARES

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
    * Datos de radiación solar: {DATOS_SOLARES}

------------------------------------
"""
    print(texto)

    continuar = input("Continuar ? [y/n]")
    if continuar != "y": sys.exit()

    num_batch_procesados = 0
    num_batch_totales    = len(Lat)

    # diccionarios para concatenar datos
    datos_GOES,datos_SOLARES = {} , {}
    for banda in BANDAS:
        datos_GOES[str(banda)] = []
    for columna in DATOS_SOLARES:
        datos_SOLARES[columna] = []
    
    # Obtenemos el nombre del batch (sin la extención).
    for i in range(len(Lat)):
        lat , lon = Lat[i],Lon[i]
        try:
            batch_datos_GOES,batch_datos_SOLARES = procesar_batch(lat,lon)
        except IndexError as err:
            print(f"Durante el procesamiento del batch en {lat} {lon} ha ocurrido el siguiente error:\n{err}")
        else:
            if UNIR_BATCHES:
                # Juntamos todo en un diccionario.
                for banda in BANDAS:
                    datos_GOES[str(banda)].append(batch_datos_GOES[str(banda)])
                for columna in DATOS_SOLARES:
                    datos_SOLARES[columna].append(batch_datos_SOLARES[columna])
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
            datos_GOES[str(banda)] = np.concatenate(datos_GOES[str(banda)],axis=0)
            dataset.create_dataset(name=str(banda),data=datos_GOES[str(banda)],dtype=np.float32)
        for columna in DATOS_SOLARES:
            datos_SOLARES[columna] = np.concatenate(datos_SOLARES[columna],axis=0)
            dataset.create_dataset(name=columna,data=datos_SOLARES[columna])
    
    print(f"Se ha creado el dataset {nombre_dataset()} con {len(datos_SOLARES[columna])} datos" )
    print("Script de generación de dataset terminado!")





