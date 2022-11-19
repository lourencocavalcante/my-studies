import datetime
import requests

def descargaDatos(año,mes,día,hora,hora_forecast,output_path="gfs_data.grib2"):
    """
    Descarga un dataset del GFS y lo guarda en formato
    GRIB2.
    """
    # Generamos el url de descarga con los datos proporcionados.
    fecha = datetime.datetime(año,mes,día)
    fecha = fecha.strftime("%Y%m%d")
    hora  = str(hora).zfill(2)
    hora_forecast = str(hora_forecast).zfill(3)
    url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{fecha}/{hora}/atmos/gfs.t{hora}z.pgrb2.0p25.f{hora_forecast}"
    
    # Descargamos los datos. (Aproximadamente 500Mb de datos.)
    print("Iniciando descarga...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                f.write(chunk)
    print("Descarga completada!")


def coordinates2px(lat,lon):
    """
    Dadas unas coordenadas encuentra su equivalente
    en posición de pixeles en los datos del GFS.

    Atención: Solo funciona por ahora con resolución de 0.25 grados.
    """
    resolución = 0.25

    lat_o = 90
    lon_o = 0
    shift_x = 1440 - abs(int(lon // resolución))
    shift_y = int( (lat_o - lat) // resolución )
    return shift_x , shift_y

def recortarYcentrar(array,lat,lon,ventana=40):
    """
    Recorta y centra un segmento de imágen del GFS.

    Atención: Solo funciona para resolución de 0.25
    """
    shift_x,shift_y = coordinates2px(lat,lon)
    array = array[shift_y-ventana:shift_y + ventana,shift_x-ventana:shift_x + ventana ]
    return array