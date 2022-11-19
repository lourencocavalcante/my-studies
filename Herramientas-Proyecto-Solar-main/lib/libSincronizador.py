import datetime
from os import error
import numpy as np

class DatosTemporales:
    """
    Objeto que contendrá una lista de los datos cada uno asociado a una fecha y hora.
    En el init es importante o pasarle una función para extraer las fechas (callback),
    o proporcionar directamente esta lista con los objetos datetime.
    """
    def __init__(self,identificador,lista_datos,callback=None,lista_datetime=None):
        self.identificador  = identificador
        self.lista_datos    = lista_datos
        self.número_datos   = len(lista_datos)

        # Obtenemos las fechas de los datos.
        if callback != None:
            self.lista_datetime = callback(lista_datos)
        elif type(lista_datetime) == list:
            self.lista_datetime = lista_datetime
        else:
            raise TypeError("No se especifico el parámetro callback o  el parámetro lista_datetime.")
    
class Sincronizador:
    def __init__(self,lista_DatosTemporales,verbose=False):

        # Check: Ordenenamos los datos de acuerdo a los datetimes.
        # Nota : El ordenamiento sucede inplace con los datos temporales de la lista.
        for objeto in lista_DatosTemporales:
            lista_ordenada = sorted(zip(objeto.lista_datetime , objeto.lista_datos))
            objeto.lista_datetime = [elemento[0] for elemento in lista_ordenada]
            objeto.lista_datos    = [elemento[1] for elemento in lista_ordenada]
        self.verbose = verbose
        self.lista_objetos  = lista_DatosTemporales
        # Obtenemos los datos temporales con el menor número de elementos.
        num_elementos   = np.array([objeto.número_datos for objeto in lista_DatosTemporales])
        self.índice_ref = np.argmin(num_elementos)
        # Obtenemos el objeto de referencia (el del menor número de elementos)
        self.obj_referencia  = lista_DatosTemporales[self.índice_ref]
        self.último_indice   = [0 for i in range(len(self.lista_objetos))] # --> Matriz que tiene tiene los indices de sincronización.

    def _sincronizar(self,umbral_segundos):
        """
        Devuelve una tupla con los índeces en el que un objeto de cada grupo de DatosTenmporales
        está sincronizado bajo el rango de un umbral.
        """
        while True:
            error_sincronización = False # --> Marca cuando hay un error en la sincronización con algún objeto.
            # Obtenemos la fecha de sincronización.
            índice_sinc = self.último_indice[self.índice_ref]
            fecha_sinc  = self.lista_objetos[self.índice_ref].lista_datetime[índice_sinc]
            for índice_objeto in range(len(self.lista_objetos)):
                # Obtenemos la fecha del objeto.
                fecha_objeto = self.lista_objetos[índice_objeto].lista_datetime[self.último_indice[índice_objeto]]
                # Calculamos el desface temporal.
                desface_temporal = (fecha_sinc - fecha_objeto).total_seconds()
                # Intentamos hacer sincronización con cada objeto empezando por el último índice.
                if abs(desface_temporal) <= umbral_segundos:
                    continue
                # Desfece temporal negativo, fecha del objeto adelante del de referencia.
                # --> Empezamos búsqueda hacia atras.
                elif desface_temporal < 0:
                    if self.verbose: print("Desface negativo")
                    # Buscamos candidatos a sincronización 
                    while abs(desface_temporal) > umbral_segundos:
                        self.último_indice[índice_objeto] -= 1
                        # Check: índice llego a 0.
                        if self.último_indice[índice_objeto] < 0:
                            self.último_indice[índice_objeto] = 0
                            error_sincronización = True
                            break
                        try:
                            fecha_objeto     = self.lista_objetos[índice_objeto].lista_datetime[self.último_indice[índice_objeto]]
                            desface_temporal = (fecha_sinc - fecha_objeto).total_seconds()
                        except IndexError:
                            error_sincronización = True
                            break
                # Desface de tiempo positivo, fecha de objeto atras del de referencia.
                # --> Empezamos búsqueda hacia adelante.
                elif desface_temporal > 0:
                    if self.verbose: print("Desface positivo")
                    while abs(desface_temporal) > umbral_segundos:
                        self.último_indice[índice_objeto] += 1
                        try:
                            fecha_objeto     = self.lista_objetos[índice_objeto].lista_datetime[self.último_indice[índice_objeto]]
                            desface_temporal = (fecha_sinc - fecha_objeto).total_seconds()
                        except IndexError:
                            error_sincronización = True
                            break  
            # Una vez revisado todos lo objetos, evaluamos si hubo algún error en la evaluación.
            if error_sincronización == True:
                if self.verbose: print("Error")
                self.último_indice[self.índice_ref] += 1 # --> Si hubo algún error, pasamos al  siguiente objeto de referencia.        
            # Si no hubo ningun error retornamos.
            else:
                índices_sincronizados = self.último_indice.copy()
                # Adelantamos los índices para la proxima búsqueda.
                for índice_objeto in range(len(self.lista_objetos)):
                     self.último_indice[índice_objeto] += 1
                return índices_sincronizados
        
    def generarSerieTiempo(self,umbral_sinc,umbral_serie,longitud=1):
        """
        Generá una serie de tiempo que devuelve como índices que despues pueden ser usados en el
        grupo de los datos para hacer un dataset con las series de tiempo.
        """
        lista_series_tiempo = [] # --> lista que tendrá todas las series de tiempo válidas.

        # Obtenemos del sincronizador todos los elementos que se pudieron sincronizar.
        lista_tuplas = []
        while True:
            try:
                tupla = self._sincronizar(umbral_sinc)
                lista_tuplas.append(tupla)
            except IndexError:
                break
        if longitud == 1: return lista_tuplas # --> retornamos si la longitud es 1.
        # Iteramos sobre cada elemento de la lista de tuplas.
        for i in range(len(lista_tuplas) - longitud + 1):
            error_de_serie  = False
            serie_de_tiempo = []
            serie_de_tiempo.append(lista_tuplas[i])
            for index_st in range(longitud - 1):
                # Obtenemos la fecha del primer elemento de la tupla.
                index_ref = lista_tuplas[i + index_st][0]
                fecha_ref = self.lista_objetos[0].lista_datetime[index_ref]
                # Obtenemos la fecha del primer elemento de la siguiente tupla.
                index = lista_tuplas[i + index_st + 1][0]
                fecha = self.lista_objetos[0].lista_datetime[index]
                # Comparamos fechas.
                desface_temporal = (fecha_ref - fecha).total_seconds()
                # Si la distancia de tiempo es menor al umbral lo añadimos a la serie de tiempo.
                if abs(desface_temporal) < umbral_serie:
                    serie_de_tiempo.append(lista_tuplas[i+index_st+1])
                else:
                    error_de_serie = True
                    break
            
            # Si no ocurrio ningun error, añadimos la serie de tiempo a la lista.
            if error_de_serie == False:
                lista_series_tiempo.append(serie_de_tiempo)

        return lista_series_tiempo



def revisar_orden_temporal(lista_datetime):
    num_elementos = len(lista_datetime)
    for i in range(num_elementos-1):
        datetime_2 = lista_datetime[i+1]
        datetime_1 = lista_datetime[i]
        if (datetime_2 - datetime_1).total_seconds() < 0:
            raise ValueError("Orden temporal de la lista no respetado!")