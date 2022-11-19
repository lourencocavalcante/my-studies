library(raster)
library(viridis)
library(rgdal)
library(sf)
library(tidyverse)
library(stringr)
library(ssh)
# library(geobr)
# library(tmap)


# system("rm *C0* pixel_valor.csv")
set.seed(13)
loc_plant <- read.table("../canasat/sp_12.txt") %>% 
  sample_n(1) %>%
  st_as_sf(coords = c(2,1), crs=crs("+init=epsg:4326 +proj=longlat +ellps=WGS84", asText=TRUE))

# plant <- st_read("../canasat/Canasat_CS_2012/CS_2012.shp")
# plant <- st_transform(plant, crs = crs(ndvi_rast, asText=TRUE))
# plant <- sample_n(plant, 1) %>% select(geometry)
# plot(plant)


# sessao <- ssh_connect("wesleysatelis@betelgeuse.cpa.unicamp.br", passwd = "LR*c4E#tz7")
# file_path <- R.home("/home/wesleysatelis/ess_server/folders/20190607/Bandas1235.tar.gz")
sessao <- ssh_connect("ess@143.106.29.111", passwd = "eects")

folderlist <- read.table("filelist.txt") %>% 
  as_tibble() %>% 
  select(V9) %>%
  filter(str_length(V9)==8)

folderlist <- pull(folderlist, V9)
folderlist <- sort(folderlist)

# print(folderlist)
# folderlist <- folderlist[1]
# print("..")
# print(folderlist)

for(folder in folderlist){
  start_time <- Sys.time()
  
  scp_download(sessao, paste("/home/ess/jurandir/", folder, "/Bandas1235.tar.gz", sep=''))
  system("tar -xf Bandas1235.tar.gz && rm Bandas1235.tar.gz")
  ssh_disconnect(sessao)
  
  files <- list.files() %>% 
    str_subset("C02.txt")
  
  for(t in files){ # mudar os arquivos
    c2 <- scan(file = t, sep = ',', quiet=T)
    c2 <- matrix(c2, byrow= TRUE, ncol = 2110, nrow = 1332)
    
    band3 <- str_replace(t, "C02.txt", "C03.txt")
    
    if(file.exists(band3)){
      c3 <- scan(file = str_replace(t, "C02.txt", "C03.txt"), sep = ',', quiet=T)
      c3 <- matrix(c3, byrow= TRUE, ncol = 2110, nrow = 1332)
    }else{
      next
    }
    
    ndvi <- t(c3-c2)/t(c3+c2)
    
    # write.matrix(ndvi, paste("/media/Wesley/5096-1F98/20190611/Bandas1235/NDVI/", t, "_NDVI.txt", sep=''), sep = "\t")
    
    ndvi_rast <- raster(xmn=-53.4948231956, xmx=-43.9471907179,
                        ymn=-25.4224855885, ymx=-19.4198207653, ncols=2110, nrows=1332,
                        crs="+init=epsg:4326 +proj=longlat +ellps=WGS84")
    ndvi_rast <- setValues(ndvi_rast, as.vector(ndvi))
    ndvi_rast <- flip(ndvi_rast, 2)
    
    ndvi_rast_mtr <- projectRaster(ndvi_rast, crs="+proj=utm +zone=22 +south +datum=WGS84 +units=m +no_defs")
    loc_plant <- st_transform(loc_plant, crs = crs(ndvi_rast_mtr, asText=TRUE))
    loc_plant_2km <- st_buffer(loc_plant, dist=500) # dist: raio em metros
    
    # print(t)
    
    # SALVAR RASTERS POR PONTO DE INTERESSE
    for(plant in seq(1,nrow(loc_plant_2km))){
      raio <- crop(ndvi_rast_mtr, filter(loc_plant_2km, row_number() == plant))
      # writeRaster(raio, paste("../ndvi/", plant, '_', str_sub(t, 1, 4), '.', str_sub(t, 5, 6), '.', str_sub(t, 7, 8),
      #                   '_', str_sub(t, 9, 10), '_', str_sub(t, 11, 12),  "_NDVI.tif", sep=''),
      #             format="GTiff", overwrite=TRUE)
      vals <- getValues(raio)
      
      # locVals_mtr_p <- getValuesBlock(ndvi_rast_raio, format="matrix", nrows=nrow(ndvi_rast_raio)) # matriz
      vals_rows <- tibble::enframe(vals) %>%
        spread(value = value, key = name) %>% 
        mutate(data=paste(str_sub(t, 1, 4), '.', str_sub(t, 5, 6), '.', str_sub(t, 7, 8), sep=''), 
               hora=paste(str_sub(t, 9, 10), ':', str_sub(t, 11, 12), sep=''), pixel=plant)
      
      if(exists("valsTempo")) {
        valsTempo <- bind_rows(valsTempo, vals_rows)
      } else {
        valsTempo <- vals_rows
        # print("inicio")
        # vals
      }
    }
    
    if(file.exists("pixel_valor.csv")){
      write_csv(valsTempo, "pixel_valor.csv", append = T)
    } else{
      write_csv(valsTempo, "pixel_valor.csv", col_names = T)
    }
  }
  system("rm *C0*")
  end_time <- Sys.time()
  # print(paste(folder, end_time - start_time, "mins"), sep=' ')
}
