import lib.libGOES
import datetime
import netCDF4
import numpy as np


# Definimos la fecha de inicio y final de la descarga.
fecha_inicio = datetime.datetime(2020,1,1,17,0)
fecha_final  = datetime.datetime(2020,1,1,18,0)

# Elegimos el producto de descarga como la imagen de CONUS (producto "ABI-L1b-RadC") con la banda 3 y descargamos con la función.
lib.libGOES.descargaIntervaloGOES16(producto        = "ABI-L1b-RadC",
                                    datetime_inicio = fecha_inicio,
                                    datetime_final  = fecha_final,
                                    banda = 3 ,
                                    output_path = "NETCDF_DATA/")