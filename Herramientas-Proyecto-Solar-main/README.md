# Herramientas para el manejo de datos satelitales y de radiación solar :earth_americas:

![alt text](https://github.com/FelosRG/Herramientas-Proyecto-Solar/blob/main/Figuras/portada_GOES16.jpg?raw=true)

<b> ! Nota para Adrián : Revisar que el código no contenga API-keys privadas antes de actualizar!</b> <br> <br>

## Contenido :writing_hand:

  - [Objetivos](#objetivos)
  - [Instalación de dependencias](#instalación-de-dependencias)
  - [Descarga de datos satelitales]()
  - [Manual de generación de datasets](#manual-de-generación-de-datasets)
  - [Tutorial de generación de datasets](#tutorial-de-generación-de-dataset)
  - [Tutorial de visualización de datasets](#tutorial-de-visualización-del-dataset)

## Objetivos
En este repositorio están herramientas para la adquisición y manejo de datos satelitales provenientes del satélite GOES-16 y datos de radiación solar con el objetivo de la creación de datasets para el entrenamiento de modelos de inteligencia artificial para la predicción de la radiación solar. <br>

## Instalación de dependencias
**Se recomienda el uso de Anaconda (Python3)**<br>
Una vez clonado (o descargado) el repositorio, entramos en él y ejecutamos el siguiente comando con pip para instalar todas las dependencias requeridas:

Si se tiene anaconda
``` 
conda install requeriments.txt
```
Sin anaconda
``` 
pip3 install requeriments.txt
```
Después de instalar las dependencias es necesario conseguir una API-KEY del Nation Solar Radiation Database para la descarga de los datos de radiación solar en https://developer.nrel.gov/signup/

Una vez se tenga la API-KEY se necesita editar un par de campos en el script ubicado en **lib/libNSRDB.py** de la siguiente forma:
``` 
API_KEY = "abcdef12345"
EMAIL   = 'ejemplo@jemplo.com'
```

## Guía de descarga de datos satelitales

En el repositorio hay dos notebooks que sirven como guía para la descarga de imágenes en el archivo histórico de una fecha o momento en el pasado, y otra para la descarga de la imágen más reciente.

Ambos notebooks también son una pequeña guía para el uso de las herramientas de manipulación de imágenes satélitales desarrolladas en la liberia libGOES.py

Por ejemplo:
Con las herramientas de descarga y manipulación es posible encontrar la posición en la imágen de una coordenadas geográficas así como hacer "zoom" alrededor de ese punto.

En la siguiente imágen descargada fue ubicada el lago de chapala a travéz de las coordenadas con la función **lib.libGOES.coordinates2px**

<p align="center">
 <img src="https://github.com/FelosRG/Herramientas-Proyecto-Solar/blob/main/Figuras/imagen_satelital.png?raw=true" />
</p>

para luego hacer "zoom" con **lib.GOES.cortarYcentrar**

<p align="center">
 <img src="https://github.com/FelosRG/Herramientas-Proyecto-Solar/blob/main/Figuras/lago_de_chapala.png?raw=true" />
</p>

## Manual de generación de datasets
Es posible generar datasets con información de múltiples bandas y de radiación solar, para conseguir una dataset en la carpeta **Datasets/** están los siguientes scripts que deben de ser ejecutados en el siguiente orden

* **config.py**<br>
  En este script se colocan las configuración principales para la descarga de los datos satelitales y de radiación solar así un primer pre-procesado de los datos satelitales.<br>

  Tras su ejecución se creará un archivo **config.pickle** que contendrá  parte de las configuraciones realizadas.

  **Antes de su ejecución es necesario modificar los ajustes que se deseen**

* **descarga_GOES.py**<br>
  Descarga los datos satelitales según las configuraciones establecidas en **config.py** los archivos descargados se encontrarán en la carpeta **Datasets/Descargas/GOES/**

* **descarga_NSRDB.py**<br>
Descarga de los datos de radiación solar del National Solar Radiation Database (NSRDB) según las configuraciones establecidas en **config.py**

* **pre-procesado_GOES.py**<br>
  Realiza un primer procesado de los datos satelitales para facilitar los siguientes pasos.

* **separador_GOES.py**
  Clasifica los datos según las localizaciones, este es el paso final previo a la generación de el dataset.

* **gen_dataset.py**<br>
Antes de ejecutar este script se necesitan colocar las configuraciones deseadas como
  * Las bandas que se usarán en el dataset.
  * Tamaño de las imágenes satelitales alrededor de cada punto.
  * Si el dataset será de una serie de tiempo y de qué longitud será esta serie de tiempo.
  
  Una vez colocada estas configuraciones al principio del script se puede ejecutar el script.

  El dataset generado se encontrará en la carpeta **Datasets/Datasets/**  y tendrá como nombre las principales configuraciones realizadas por ejemplo:<br>

  **Ventana_5-Bandas_4_6_-Secuencia_1-Resolucion_5-NSRDB.h5**
  
  Que significa:
  * [Ventana] Las imágenes del dataset están compuestas por imágenes de 5px de ventana (10x10 px de tamaño)
  * [Bandas] El dataset contiene datos de la banda 4 y 6 del satélite GOES
  * [Secuencia] El dataset está compuesto por series de tiempo de 1 de longitud.
  * [Resolución] El grid con la que se dividió la región especificada fue de 5x5.
  * [NSRDB] Significa que los datos solares provienen del National Solar Radiation Database. (Próximamente quiero implementar otras fuentes de datos de radiación solar)

Notar que el dataset está en formato h5, que es posible abrir con la librería h5py, de la siguiente forma:

```python 
import h5py

# nombre ejemplo
nombre_dataset = Ventana_5-Bandas_4_6_-Secuencia_1-Resolucion_5-NSRDB.h5

# Para ver los nombre de las variables disponibles dentro del dataset
with h5py.File(nombre_dataset,"r") as dataset:
  print(dataset.keys())

# Para extraer los datos de una variable
with h5py.File(nombre_dataset,"r") as dataset:
  variable = dataset["nombre de la variable"][()]
```

Todas las variables se devuelven en numpy arrays <br><br>


## Tutorial de generación de dataset

Para generar un dataset vamos a primero cambiar las siguientes configuraciónes  en **config.py** <br>

```python
DÍAS = 1        # Para descargar solo un día del año de datos satelitales.
BANDAS = [4,13] # Pero puede ser cualquier otro par de bandas

# Descargamos los datos entre las horas de la 1pm y 2pm hora de México. (El intervalo es arbitrario)
HORA_INICIO_UTC , MIN_INICIO_UTC = 18 , 00
HORA_FINAL_UTC  , MIN_FINAL_UTC  = 19 , 00

# Dividimos a la región especificada en un grid 5x5, cada intersección del grid es un lugar de donde se generarán los datos del dataset.
RESOLUCIÓN = 5

VENTANA_RECORTE = 100

# Las otras configuraciones las dejamos como están.
```

Guardamos config.py y ejecutamos los siguientes scripts en el siguiente orden:

* config.py
* descarga_GOES.py
* descarga_NSRDB.py
* pre-procesado.py
* separador.py

Después modificamos las configuraciones en **gen_dataset.py**

```python
# El dataset estará conformado por información de las bandas 4 y 13
BANDAS  = [4,13]

# Utilizaremos los 60 pixeles de ventana de la ventana de recorte puesta en config.py
VENTANA = 60

# Información de los datos del NSRDB que ocuparemos en la generación de nuestro dataset
DATOS_NSRDB = ["GHI","Solar Zenith Angle","Clearsky GHI"]

# Las otras configuraciones las dejamos como están.
```

Guardamos y ejecutamos **gen_dataset.py**, una vez finalizado el procesado tendremos nuestro dataset en **Datasets/Datasets/** llamado<br>

**Ventana_200-Bandas_4_13-Secuencia_1-Resolucion_5-NSRDB.h5**

<br><br>

## Tutorial de visualización del dataset

Ya con el dataset generado movemos el dataset (o lo descargamos a nuestra computadora si se está trabajando en una computadora remota) a una carpeta aparte donde crearemos un script o notebook de python

Con los siguiente:

```python
import h5py
import matplotlib.pyplot as plt

# Extraemos los datos del dataset
nombre_dataset = "Ventana_60-Bandas_4_13_-Secuencia_1-Resolucion_5-NSRDB.h5"
with h5py.File(nombre_dataset,"r") as dataset:
    banda_4  = dataset["4"][()]
    banda_13 = dataset["13"][()]
    GHI   = dataset["GHI"][()]

# Extraemos los datos de un mismo momento y lugar usando el mismo index

# Por ejemplo banda_4[i] y banda_13[i] y GHI[i] corresponden a las imágenes de la banda 4 y banda 13  y la readición solar del mismo momento en el mismo lugar.

fig, ax = plt.subplots(2,3,figsize=(14,8))
for i in range(3):
    ax[0,i].imshow(banda_4[i])
    ax[0,i].set_title("Banda 4",loc="left",weight="bold")
    ax[0,i].set_title(f"t={i}",loc="center")
    ax[0,i].set_title(f"GHI={GHI[i]}",loc="right")
    ax[0,i].axis("off")
    
    ax[1,i].imshow(banda_13[i])
    ax[1,i].set_title("Banda 13",loc="left",weight="bold")
    ax[1,i].set_title(f"t={i}",loc="center")
    ax[1,i].set_title(f"GHI={GHI[i]}",loc="right")
    ax[1,i].axis("off")
```

Y como se pude ver en el resultado, le hemos asociado el dato de radiación solar a cada una de las imágenes.

**Nota: La información de la radiación solar es del centro de la imágen.**

![alt text](https://github.com/FelosRG/Herramientas-Proyecto-Solar/blob/main/Figuras/dataset.png?raw=true)










