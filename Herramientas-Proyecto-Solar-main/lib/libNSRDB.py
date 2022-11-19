# Configuración de usuario.
API_KEY = "gfYiPMGMLLOMK6h8PcSp2102kPZrFFwFIqp5vSM9"
EMAIL   = "felos@ciencias.unam.mx"
# -------------------------------------------


import pandas as pd
import numpy  as np
import math

if API_KEY == None:
    raise ValueError("No se ha ingresado una API-KEY del NSRDB!, es necesario solicitar una y colocarla en lib/libNSRDB.py")
if EMAIL == None:
    raise ValueError("No se ha colocado un email en lib/libNSRDB.py")

def getData(lat,lon,year,intervalo=60,UTC=False):
    " Función que obtiene los datos de un único punto."

    api_key    =  API_KEY
    interval   =  intervalo

    if UTC:
    	utc = "true"
    else:
    	utc = 'false'
    
    email = EMAIL
    # Se ocupa la url_base adecuada para el tipo de intervalo.
    if intervalo >= 30:
        url_base = "https://developer.nrel.gov/api/solar/nsrdb_psm3_download.csv?"
        #url_base =  "https://developer.nrel.gov/api/nsrdb/v2/solar/full-disc-download.csv?"
    else:
        url_base = "https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-5min-download.csv?"
    parametros = f"wkt=POINT({lon}%20{lat})&names={year}&interval={interval}&utc={utc}&email={email}&api_key={api_key}"
    url = url_base + parametros
    try:
    	df_data = pd.read_csv(url,skiprows=2)
    except:
        print(f"Link fallido: {url}")
        raise
    return df_data 

def getDataTMY(lat,lon):
    " Función que obtiene los datos de un único punto."
    
    api_key          = API_KEY
    utc              = 'false'
    email = EMAIL
    url = f'https://developer.nrel.gov/api/nsrdb/v2/solar/psm3-tmy-download.csv?wkt=POINT({lon}%20{lat})&names=tmy-2019&utc={utc}&email={email}&api_key={api_key}'
    return pd.read_csv(url,skiprows=2)

def TiempoSol(lat,num_dia_año):
    "Obtiene la duración del día en minutos de una latitud y en un día del año en partícular."
    
    # Ángulo de declinación de la tierra.
    epsilon = 23.5
    # Pasamos a radianes
    epsilon = (math.pi / 180)*epsilon
    lat     = (math.pi / 180)*lat
    #Pasamos de fecha con inicio en solticio invierno a fecha normal
    num_dia_año = num_dia_año + 10
    dif = num_dia_año - 365
    if dif > 0:
        num_dia_año = 365 + dif
    # Obtenemos gamma
    gamma   = np.arccos( -np.sin(epsilon)*np.cos(2*math.pi*num_dia_año / 365) )
    # Obtenemos la duración de la media noche astronómica.
    Po      = 86400 # Segundos en un día.
    tiempo_noche = (Po / math.pi)*np.arccos(np.tan(lat)/np.tan(gamma))
    tiempo_dia   =  Po - tiempo_noche
    # Pasamos a minutos
    return tiempo_dia / 60

def PromData(df_data,lat,intervalo):
    "Obtenemos un dataframe con los valores promedidados por día."
    
    # Parámetros iniciales.
    num_intervalos_dia = int(60*24 / intervalo)
    iteraciones = int(len(df_data) / num_intervalos_dia)
    columnas    = list(df_data.columns) + ["Duración Día"]
    columnas    = ["Month","Day","Dew Point","DHI Prom","DNI Prom","GHI Prom","Pressure","Temperature","Wind Speed","Duración Día","Radiación Total"]
    df_prom     = pd.DataFrame(columns=columnas)
    # Iteracion sobre cada día del año.
    for i in range(iteraciones):
        # Obtenemos los indices del slice.
        max_index = (i+1)*num_intervalos_dia
        min_index = max_index - num_intervalos_dia
        # Separamos en un dataframe por cada día
        df  = df_data.iloc[min_index:max_index]
        # Obtenemos lso datos de la fecha.
        mes = df["Month"][min_index]
        dia = df["Day"  ][min_index]
        # Obtenemos los datos de los parámetros.
        dhi = df["DHI"].values
        dni = df["DNI"].values
        ghi = df["GHI"].values
        pressure    = df["Pressure"].values
        temperature = df["Temperature"].values
        dew_point   = df["Dew Point"].values
        wind_speed  = df["Wind Speed"].values
        # Obtenemos el número de intervalos con sol y el tiempo con luz solar.
        tiempo_sol         =  TiempoSol(lat,i)
        num_intervalos_sol =  tiempo_sol / intervalo
        radiacion_total    =  np.sum(ghi)*intervalo / 60 
        # Obtenemos el promedio de DHI y DNI de los no 0.
        dni = np.sum(dni) / num_intervalos_dia
        dhi = np.sum(dhi) / num_intervalos_dia
        ghi = np.sum(ghi) / num_intervalos_dia
        # Obtenemos el promedio de los demas parámetros.
        pressure    = np.mean(pressure) 
        temperature = np.mean(temperature)
        dew_point   = np.mean(dew_point)
        wind_speed  = np.mean(wind_speed)
        # Añadimos al dataframe
        lista_datos = [mes,dia,dew_point,dhi,dni,ghi,pressure,temperature,wind_speed,tiempo_sol,radiacion_total]
        df_añadir   = pd.DataFrame([lista_datos],columns=columnas)
        df_prom     = pd.concat([df_prom,df_añadir],ignore_index=True)
    return df_prom

def getPromDataAños(lat,lon,años=[2019]):
    "Obtenemos un dataframe con los valores promedidados por día."
   
    # Valores iniciales de los promedios
    dhi_años  = np.zeros((365,))
    dni_años  = np.zeros((365,))
    ghi_años  = np.zeros((365,))
    temperature_años   = np.zeros((365,))
    dew_point_años     = np.zeros((365,))
    pressure_años      = np.zeros((365,))
    windspeed_años     = np.zeros((365,))
    radiacion_total_años = np.zeros((365,))
    # Iteramos sobre cada año
    lista_ghi       = []
    lista_rad_total = []
    for año in años:
        # Obtenemos datos de ese año.
        df_data = getData(lat,lon,año,intervalo=60)
        #Obtenemos los promedios de ese año.
        df_prom = PromData(df_data,lat,intervalo=60)
        # Obtenemos una suma para los promedios
        dhi_años  += df_prom["DHI Prom"].values
        dni_años  += df_prom["DNI Prom"].values
        ghi_años  += df_prom["GHI Prom"].values
       
        #Añadimos datos para obtener la desviación estandar.
        lista_ghi.append(df_prom["GHI Prom"].values)
        lista_rad_total.append(df_prom["Radiación Total"].values.astype('float'))
        
        pressure_años      += df_prom["Pressure"].values
        temperature_años   += df_prom["Temperature"].values
        dew_point_años     += df_prom["Dew Point"].values
        windspeed_años     += df_prom["Wind Speed"].values
        radiacion_total_años += df_prom["Radiación Total"].values.astype('float')
    #Obtenemos la desviación estandar del ghi
    array_ghi = np.array(lista_ghi)
    array_rad_total = np.array(lista_rad_total)
    ghi_std   = np.std(array_ghi,axis=0)
    radiacion_total_std   = np.std(array_rad_total,axis=0)
    # Obtenemos el promedio de los años.
    dhi_años  /= len(años)
    dni_años  /= len(años)
    ghi_años  /= len(años)
    pressure_años      /= len(años)
    temperature_años   /= len(años)
    dew_point_años     /= len(años)
    windspeed_años     /= len(años)
    radiacion_total_años /= len(años)
    # Datos adicionales
    columna_mes    = df_prom["Month"].values
    columna_dia    = df_prom["Day"  ].values
    columna_tiempo = df_prom["Duración Día"].values
    # Columnas del nuevo dataframe
    columnas = list(df_prom.columns) + ["GHI std","Radiación Total std"]
    datos    = list(zip(columna_mes,columna_dia,dew_point_años,dhi_años,dni_años,ghi_años,pressure_años,temperature_años,windspeed_años,columna_tiempo,radiacion_total_años,ghi_std,radiacion_total_std))
    #datos = np.array([columna_mes,columna_dia,dew_point_años,dhi_años,dni_años,pressure_años,temperature_años,windspeed_años,columna_tiempo]).T
    df_prom_años  = pd.DataFrame(datos,columns=columnas)
    return df_prom_años
    
def getPromDataAños2(lat,lon,prom_rad,años=[2019]):
    "Obtenemos un dataframe con los valores promedidados por día."
   
    # Valores iniciales de los promedios
    dhi_años  = np.zeros((365,))
    dni_años  = np.zeros((365,))
    ghi_años  = np.zeros((365,))
    temperature_años   = np.zeros((365,))
    dew_point_años     = np.zeros((365,))
    pressure_años      = np.zeros((365,))
    windspeed_años     = np.zeros((365,))
    radiacion_total_años = np.zeros((365,))
    # Iteramos sobre cada año
    lista_ghi       = []
    lista_rad_total = []
    for año in años:
        # Obtenemos datos de ese año.
        df_data = getData(lat,lon,año,intervalo=60)
        #Obtenemos los promedios de ese año.
        df_prom = PromData(df_data,lat,intervalo=60)
        # Obtenemos una suma para los promedios
        dhi_años  += df_prom["DHI Prom"].values
        dni_años  += df_prom["DNI Prom"].values
        ghi_años  += df_prom["GHI Prom"].values
       
        #Añadimos datos para obtener la desviación estandar.
        lista_ghi.append(df_prom["GHI Prom"].values)
        lista_rad_total.append(df_prom["Radiación Total"].values.astype('float') - prom_rad)
        
        pressure_años      += df_prom["Pressure"].values
        temperature_años   += df_prom["Temperature"].values
        dew_point_años     += df_prom["Dew Point"].values
        windspeed_años     += df_prom["Wind Speed"].values
        radiacion_total_años += df_prom["Radiación Total"].values.astype('float') - prom_rad
    #Obtenemos la desviación estandar del ghi y rad total
    array_ghi = np.array(lista_ghi)
    array_rad_total = np.array(lista_rad_total)
    ghi_std   = np.std(array_ghi,axis=0)
    radiacion_total_std   = np.std(array_rad_total,axis=0)
    # Obtenemos el promedio de los años.
    dhi_años  /= len(años)
    dni_años  /= len(años)
    ghi_años  /= len(años)
    pressure_años      /= len(años)
    temperature_años   /= len(años)
    dew_point_años     /= len(años)
    windspeed_años     /= len(años)
    radiacion_total_años /= len(años)
    # Datos adicionales
    columna_mes    = df_prom["Month"].values
    columna_dia    = df_prom["Day"  ].values
    columna_tiempo = df_prom["Duración Día"].values
    # Columnas del nuevo dataframe
    columnas = list(df_prom.columns) + ["GHI std","Radiación Total std"]
    datos    = list(zip(columna_mes,columna_dia,dew_point_años,dhi_años,dni_años,ghi_años,pressure_años,temperature_años,windspeed_años,columna_tiempo,radiacion_total_años,ghi_std,radiacion_total_std))
    #datos = np.array([columna_mes,columna_dia,dew_point_años,dhi_años,dni_años,pressure_años,temperature_años,windspeed_años,columna_tiempo]).T
    df_prom_años  = pd.DataFrame(datos,columns=columnas)
    return df_prom_años

def getPromDataAños3(lat,lon,prom_rad,años=[2019]):
    "Obtenemos un dataframe con los valores promedidados por día."
   
    # Valores iniciales de los promedios
    dhi_años  = np.zeros((365,))
    dni_años  = np.zeros((365,))
    ghi_años  = np.zeros((365,))
    temperature_años   = np.zeros((365,))
    dew_point_años     = np.zeros((365,))
    pressure_años      = np.zeros((365,))
    windspeed_años     = np.zeros((365,))
    radiacion_total_años = np.zeros((365,))
    # Iteramos sobre cada año
    lista_ghi       = []
    lista_rad_total = []
    for año in años:
        # Obtenemos datos de ese año.
        df_data = getData(lat,lon,año,intervalo=60)
        #Obtenemos los promedios de ese año.
        df_prom = PromData(df_data,lat,intervalo=60)
        # Obtenemos una suma para los promedios
        dhi_años  += df_prom["DHI Prom"].values
        dni_años  += df_prom["DNI Prom"].values
        ghi_años  += df_prom["GHI Prom"].values
       
        #Añadimos datos para obtener la desviación estandar.
        lista_ghi.append(np.abs(df_prom["GHI Prom"].values - prom_rad))
        lista_rad_total.append(df_prom["Radiación Total"].values.astype('float'))
        
        pressure_años      += df_prom["Pressure"].values
        temperature_años   += df_prom["Temperature"].values
        dew_point_años     += df_prom["Dew Point"].values
        windspeed_años     += df_prom["Wind Speed"].values
        radiacion_total_años += np.abs(df_prom["Radiación Total"].values.astype('float') - prom_rad)
    #Obtenemos la desviación estandar del ghi y rad total
    array_ghi = np.array(lista_ghi)
    array_rad_total = np.array(lista_rad_total)
    ghi_std   = np.std(array_ghi,axis=0)
    radiacion_total_std   = np.std(array_rad_total,axis=0)
    # Obtenemos el promedio de los años.
    dhi_años  /= len(años)
    dni_años  /= len(años)
    ghi_años  /= len(años)
    pressure_años      /= len(años)
    temperature_años   /= len(años)
    dew_point_años     /= len(años)
    windspeed_años     /= len(años)
    radiacion_total_años /= len(años)
    # Datos adicionales
    columna_mes    = df_prom["Month"].values
    columna_dia    = df_prom["Day"  ].values
    columna_tiempo = df_prom["Duración Día"].values
    # Columnas del nuevo dataframe
    columnas = list(df_prom.columns) + ["GHI std","Radiación Total std"]
    datos    = list(zip(columna_mes,columna_dia,dew_point_años,dhi_años,dni_años,ghi_años,pressure_años,temperature_años,windspeed_años,columna_tiempo,radiacion_total_años,ghi_std,radiacion_total_std))
    #datos = np.array([columna_mes,columna_dia,dew_point_años,dhi_años,dni_años,pressure_años,temperature_años,windspeed_años,columna_tiempo]).T
    df_prom_años  = pd.DataFrame(datos,columns=columnas)
    return df_prom_años

