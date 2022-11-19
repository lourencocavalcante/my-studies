# Libería con funciones auxiliares.
import os
import datetime
import netCDF4
import numpy as np
import geopandas as geopd
from   shapely.geometry import Point

import lib.libGOES as GOES

def check_poligono(geopd,point_x,point_y):
    """ Revisa si un punto está dentro de algun poligono del geopandas.
        Salida (bool)
        ! Falta optimizar.
    """
    p = Point(point_x,point_y)
    result = False
    for polygon in geopd["geometry"]:
        if result == True:
            break
        else:
            result = p.within(polygon)
    return result

def generar_mask_espacial(
    INF_LON,SUP_LON,
    INF_LAT,SUP_LAT,
    RESOLUCIÓN,
    PATH_SHAPEFILE):
    """
    Genera 3 arrays, Lon , Lat contendrán coordenadas dentro de
    el cuadro definido por los puntos de las coordenadas igresadas
    como argumento, mask_espacial contiene un array booleano (un mask)
    con valores positivos para los puntos que pertenecen a la república
    mexicana.
    """
    shapefile_mexico = geopd.read_file(PATH_SHAPEFILE)
    X   = np.linspace(INF_LON , SUP_LON , RESOLUCIÓN)
    Y   = np.linspace(INF_LAT , SUP_LAT , RESOLUCIÓN)
    Lon , Lat = np.meshgrid(X,Y) # El meshgrid es que nos proporciona las coordendas del grid.

    mask_espacial  = np.zeros(Lon.shape)
    for i in range(Lon.shape[0]):
        for j in range(Lon.shape[1]):
            mask_value          = check_poligono(shapefile_mexico,Lon[i,j],Lat[i,j])
            mask_espacial[i,j]  = mask_value
    
    return Lon,Lat,mask_espacial

def generar_dias_año(dias):
    """
    Genera un conjunto de días espaciados, a lo largo del año.
    """
    return np.linspace(0,364,dias).astype(int)

def asignarNombreArchivo(lat,lon,extensión="csv"):
    """
    Genera un nombre de archivo con las coordenadas del lugar de donde
    son los datos y que se guardarán bajo ese nombre.
    """
    lat = round(lat,4)
    lon = round(lon,4)
    nombre = f"{lat}_{lon}.{extensión}"
    return nombre

def obtenerIntervaloUTC(
                        dia_delta,
                        HORA_INICIO_UTC,
                        MIN_INICIO_UTC,
                        HORA_FINAL_UTC,
                        MIN_FINAL_UTC
                       ):
    """
    Obtiene el intervalo de descargas.
    """
    fecha_inicio = datetime.datetime(2020,1,1,HORA_INICIO_UTC,MIN_INICIO_UTC)
    fecha_inicio = fecha_inicio + datetime.timedelta(days=dia_delta)
    fecha_final  = datetime.datetime(2020,1,1,HORA_FINAL_UTC,MIN_FINAL_UTC)
    fecha_final  = fecha_final + datetime.timedelta(days=dia_delta)
    return fecha_inicio , fecha_final

class archivosGOES:
    """
    Define el objeto que contiene la información de los archivos de cada
    tipo de producto del GOES.
    """
    def __init__(self,producto,abreviatura,path="Data/NETCDF/",banda=None):
        self.producto    = producto
        self.abreviatura = abreviatura
        self.banda = banda
        self.path  = path + self.producto + "/"

        if banda != None:
            self.path = self.path + f"Banda{banda}" + "/"
        
        # Obtenemos la lista de archivos.
        lista_archivos = os.listdir(self.path)
        lista_archivos.sort()
        
        self.lista_archivos  = lista_archivos
        self.número_archivos = len(self.lista_archivos)
        
        # Obtenemos la lista de fechas de cada archivo.
        lista_fechas = []
        for index in range(self.número_archivos):
            nc    = netCDF4.Dataset(self.path + self.lista_archivos[index])
            fecha = GOES.obtenerFecha_GOES(nc,return_datetime=True)
            nc.close()
            lista_fechas.append(fecha)
        
        self.lista_fechas = lista_fechas
        
        # Aquí almacenaremos los archivos que salgan malos.
        bad_data_index = []
        
        # Check 1 : Revisamos que el orden de las fechas esté bien --------------------------------------
        print(f"archivosGOES : Check 1 - Revisando orden correcto de las fechas para {self.abreviatura}")
        check1 = True
        for index in range(self.número_archivos - 1):
            inicio = self.lista_fechas[index]
            fin    = self.lista_fechas[index + 1]
            # Si se encuentra una fecha fuera de orden cronológico no pasa el check.
            if (fin-inicio).total_seconds() < 0:
                check1 = False
                bad_data_index.append(index)
            # Si encontramos rastro de bad data tambien no pasa el check.
            elif inicio.year == 2000:
                check1 = False
                bad_data_index.append(index)
            elif fin.year == 2000:
                bad_data_index.append(index)
                check1= False
                
        if check1:
            print("archivosGOES : Check 1 - No hubo errores.")
        else:
            print(f"archivosGOES : Check 1 - Se encontraron {len(bad_data_index)} errores \"Bad data\",se omitiran los archivos.")
        i = 0 # --> Quitar un elemento de la lista recorre los indices, hay que compensar eso.
        for bad_index in bad_data_index:
            self.lista_fechas.pop(bad_index - i)
            self.lista_archivos.pop(bad_index - i)
            i += 1
        # Actualizamos el número de archivos.
        self.número_archivos = len(self.lista_archivos)

class matcherGOES:
    """
    Mantiene la cuenta de lo necesario para la realización de los matchs entre
    los archivos.
    """
    
    def __init__(self,lista_objetos):
        
        # Obtenemos el objeto con el menor número de archivos.
        num_elementos = np.array([objeto.número_archivos for objeto in lista_objetos])
        min_elementos = np.argmin(num_elementos)
        
        # Obtenemos el objeto de referencia
        referencia = lista_objetos[min_elementos]
        print(f"matcher: El producto con el menor número de elementos es {referencia.abreviatura} con {referencia.número_archivos} elementos")
        
        self.index_referencia  = min_elementos
        self.referencia        = referencia
        self.lista_objetos     = lista_objetos
        
        # Indices con el match actual.
        self.match_indexes = [0 for i in range(len(self.lista_objetos))]
        
    def match(self):
        """
        Devuelve los index para la realización del match.
        """
        
        # Umbral para definir una máxima diferencia en el match.
        MÁXIMA_DIFERENCIA = 60*10
        
        ref_match_index  = self.match_indexes[self.index_referencia]     # --> Obtenemos el índice actual de referencia.
        fecha_referencia = self.referencia.lista_fechas[ref_match_index] # --> Obtenemos la fecha a la que apunta el índice.
        
        # Iteramos sobre cada objeto.
        for i in range(len(self.match_indexes)):
            
            hay_match = False
            while hay_match == False:
                
                # Obtenemos la fecha a la que apunta el índice actual para el objeto en iteración.
                index_fecha = self.match_indexes[i]  
                fecha = self.lista_objetos[i].lista_fechas[index_fecha] # --> Fecha del objeto actual en iteración.
            
                if (fecha_referencia - fecha).total_seconds() >= MÁXIMA_DIFERENCIA:
                    # No hay macth, movemos el index para adelante.
                    self.match_indexes[i] += 2
                    print(f"matcherGOES : Se hará desface Desface Ref:{fecha_referencia} , Match:{fecha}")
                elif (fecha_referencia - fecha).total_seconds() + 60 < 0: # --> Los 60 segundos se le agregaron para cuando el match solo está ligeramene atras.
                    print("matcherGOES : La fecha de match ha sobre pasado la fecha de referencia.")
                    print(f"            Desface Ref:{fecha_referencia} , Mat:{fecha}")
                    self.match_indexes[i] -= 1
                else:
                    # Hay match.
                    hay_match = True
        
        # Una vez que todos tuvieron match, los recorremos una casilla.
        for i in range(len(self.match_indexes)):
            self.match_indexes[i] += 1
        
        # Revertimos este recorrido nadamás para devolver el resultado.
        return list(np.array(self.match_indexes) - 1) , fecha_referencia

class InfoBanda:
    """
    Información escencial de cada banda.
    """
    def __init__(self,producto,banda,variable,fill_value,flags,índice):
        self.producto   = producto
        self.banda      = banda
        self.variable   = variable
        self.flags      = flags
        self.fill_value = fill_value
        self.identificador = self.producto + f"/Banda{self.banda}"
        self.índice = índice

    def printInfo(self):
        print(f"Producto:      {self.producto}")
        print(f"Banda:         {self.banda}")
        print(f"Variable:      {self.variable}")
        print(f"Identificador: {self.identificador}")

def split_list(a, n):
    """
    Divide una lista "a" en n partes (casi) iguales.
    Nota: Si n > len(a) devuelve las listas sobrantes vacias.
    """
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))
