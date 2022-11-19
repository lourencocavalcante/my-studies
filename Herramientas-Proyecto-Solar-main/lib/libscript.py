import lib.libGOES   as GOES
import lib.libNSRDB  as NSRDB

import numpy as np
import datetime
import netCDF4
import os

from shapely.geometry         import Point
from shapely.geometry.polygon import Polygon

def check(geopd,point_x,point_y):
    " Revisa si un punto está dentro de un estado de México."
    " Salida: True / False"
    
    p = Point(point_x,point_y)
    result = False
    for polygon in geopd["geometry"]:
        if result == True:
            break
        else:
            result = p.within(polygon)
    return result

def split_list(a, n):
    """
    Divide una lista "a" en n partes (casi) iguales.
    Nota: Si n > len(a) devuelve las listas sobrantes vacias.
    """
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

def nombre_archivo(lat,lon):
    """
    Define los nombres de los archivos del NSRDB,
    dadaas las coordenas de un punto del grid.
    """
    lat = round(lat,4)
    lon = round(lon,4)
    csv_salida = f"{lat}_{lon}.csv"
    return csv_salida

def obtenerIntervaloUTC(dia_delta   ,
                    HORA_INICIO_UTC ,
                    MIN_INICIO_UTC  ,
                    HORA_FINAL_UTC  ,
                    MIN_FINAL_UTC   ):
    """
    Obtiene el intervalo DE fechas para la descarga de datos satélitales.
    """
    fecha_inicio = datetime.datetime(2020,1,1,HORA_INICIO_UTC,MIN_INICIO_UTC)
    fecha_inicio = fecha_inicio + datetime.timedelta(days=dia_delta)
    fecha_final  = datetime.datetime(2020,1,1,HORA_FINAL_UTC,MIN_FINAL_UTC)
    fecha_final  = fecha_final + datetime.timedelta(days=dia_delta)
    return fecha_inicio , fecha_final

if __name__ == "__main__":
    lista  = list(range(2))
    result = split_list(lista,3)
    print(list(result))


class archivosGOES:
    """
    Define el objeto que contiene la información de los archivos de cada
    tipo de producto del GOES.
    """

    def __init__(self,producto,abreviatura,path="Data/NETCDF/"):
        self.producto    = producto
        self.abreviatura = abreviatura
        self.path = path + self.producto + "/"
        
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
                    print(f"matcherGOES : Se hará desface Desface Ref:{fecha_referencia} , Mat:{fecha}")
                elif (fecha_referencia - fecha).total_seconds() < 0:
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
    