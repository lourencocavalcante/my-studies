import os
import datetime
import numpy as np

def revisar_orden_temporal(lista_datetime):
    num_elementos = len(lista_datetime)
    for i in range(num_elementos-1):
        datetime_2 = lista_datetime[i+1]
        datetime_1 = lista_datetime[i]
        if (datetime_2 - datetime_1).total_seconds() < 0:
            raise ValueError(f"Orden temporal de la lista no respetado:\nDatetime 1 {datetime_1} , Datetime 2 {datetime_2}")

class DatosTemporales:
    def __init__(self,lista_datos,lista_datetime):
        self.lista_datos    = lista_datos
        self.lista_datetime = lista_datetime
        if len(lista_datos) != len(lista_datetime):
            raise ValueError(f"Las listas de datos no tienen los mismos elementos: {len(lista_datos)} , {len(lista_datetime)}")
        self.num_datos = len(lista_datos)
        # Revisamos orden temporal.
        revisar_orden_temporal(self.lista_datetime)

class Sincronizador:
    def __init__(self,lista_DatosTemporales,verbose):
        self.lista_objetos = lista_DatosTemporales
        self.num_objetos = len(self.lista_objetos)
        # Creamos una lista con los indices de sincronización.
        self.indices_sincronizacion = np.array([0 for _ in range(self.num_objetos)])
        self.iteraciones = 0

    def _buscador(self,umbral):
        # Reunimos los datetimes de los índices.
        lista_datetime_sinc = [ self.lista_objetos[i].lista_datetime[self.indices_sincronizacion[i] ] for i in range(self.num_objetos) ]
        # Obtenemos el datetime más antiguo.
        fecha_mas_vieja = min(lista_datetime_sinc)
        # Obtenemos los desfaces.
        lista_desfaces     = np.array([abs((fecha - fecha_mas_vieja).total_seconds()) for fecha in lista_datetime_sinc])
        indice_fecha_vieja = np.argmin(lista_desfaces)

        self.iteraciones += 1

        # Comparamos los desfaces.
        if np.max(lista_desfaces) <= umbral:
            # Si los desfaces estan dentro del umbral retornamos y avanzamos indices.
            lista_indices = np.copy(self.indices_sincronizacion)
            self.indices_sincronizacion += 1

            # Retornamos la lista de indices del momento generado con su fecha de referecia.
            return list(lista_indices) , fecha_mas_vieja
        else:
            # Si no se cumplieron los umbrales se adelanta un valor el índice de referencia.
            self.indices_sincronizacion[indice_fecha_vieja] += 1
            return None , None

    def _sincronizar(self,umbral):
        lista_indice = None
        while type(lista_indice) == type(None):
            lista_indice , fecha_momento = self._buscador(umbral)
        return lista_indice , fecha_momento
    
    def generarSerieTiempo(self,umbral_sinc,umbral_serie=None,longitud=1):
        if longitud == 1:
            lista_momentos = []
            while True:
                try:
                    momento , _ = self._sincronizar(umbral_sinc)
                    lista_momentos.append([momento])
                except IndexError:
                    break
            return lista_momentos
        
        if longitud > 1:
            lista_estados_momentos = []
            lista_momentos = []
            index_momentos = 0

            # Iniciamos con un momento.
            momento , fecha_momento = self._sincronizar(umbral_sinc)
            lista_momentos.append(momento)
            lista_estados_momentos.append(False)
            index_momentos += 1

            while True:
                try:
                    
                    momento , fecha_momento_nuevo = self._sincronizar(umbral_sinc)
                    lista_momentos.append(momento)
                    index_momentos += 1
                    # Vemos si se cumple el umbra de serie de tiempo.
                    if (fecha_momento_nuevo - fecha_momento).total_seconds() <= umbral_serie:
                        lista_estados_momentos.append(True)
                    else:
                        lista_estados_momentos.append(False)
                    
                    # Intercambiamos nombres para seguir con el bucle.
                    fecha_momento = fecha_momento_nuevo
                
                except IndexError:
                    break

            # Para este punto tenemos una lista de momentos y una lista de estados de momento.
            # Lo siguiente es formar las secuencias.
            lista_series_de_tiempo = []
            for i in range(len(lista_momentos) - longitud - 1):

                # Almacenamos los estados de los (longitud - 1) momentos siguientes.
                serie_tiempo_estados = np.array(lista_estados_momentos[i+1:i+longitud])

                # Si todos son true, entonces tenemos una serie de tiempo!
                if np.sum(serie_tiempo_estados) == longitud - 1:
                    serie_tiempo = lista_momentos[i:i+longitud]
                    lista_series_de_tiempo.append(serie_tiempo)
        
            return lista_series_de_tiempo
                





        




