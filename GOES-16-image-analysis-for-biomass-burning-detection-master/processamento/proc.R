library(raster)
library(viridis)
# library(rgdal)
library(geobr)
library(tmap)
library(sf)
library(tidyverse)


# setwd("/home/wesley/Desktop/teste_cpa_2018_level1b/")

# set.seed(1)
crs_latlon <- '+proj=longlat +ellps=WGS84 +towgs84=0,0,0 +no_defs'
# crs_m <- "+proj=utm +zone=22S +datum=WGS84 +units=m +no_defs +towgs84=0,0,0"

# filtrar pontos com utm 22 e utm 23
# loc_plant <- read.table("canasat/sp_12.txt") %>%
#   sample_n(10) %>% 
#   st_as_sf(coords = c(2,1), crs=crs_latlon)

c2 <- scan(file = paste("201907141630G16.SP_Bandas_2_3--L1B.pic.C02.txt", sep = ""), sep = ",", quiet=T)
c2 <- matrix(c2, byrow= TRUE, ncol = 2110, nrow = 1332)

c3 <- scan(file = paste("201907141630G16.SP_Bandas_2_3--L1B.pic.C03.txt", sep = ""), sep = ",", quiet=T)
c3 <- matrix(c3, byrow= TRUE, ncol = 2110, nrow = 1332)
ndvi <- t(c3-c2)/t(c3+c2)

ndvi_rast <- raster(xmn=-53.4948231956, xmx=-43.9471907179, ymn=-25.50, ymx=-19.50, 
                    ncols=2110, nrows=1332, crs=crs_latlon)

ndvi_rast <- raster(xmn=-53.50, xmx=-44.00, ymn=-25.4224855885, ymx=-19.4198207653, 
                    ncols=2110, nrows=1332, crs=crs_latlon)

ndvi_rast <- setValues(ndvi_rast, as.vector(ndvi))
ndvi_rast <- flip(ndvi_rast, 2)

# ==================== extraindo pixels em volta ====================
# locVals <- raster::extract(x=ndvi_rast, y=loc_plant, buffer=1000, df=T) %>% 
#   as_tibble() %>% 
#   group_by(ID) %>% 
#   mutate(pixel=paste0("pixel_", str_pad(seq(1, length(ID), 1), width=2, pad="0", side="left") )) %>% 
#   arrange(pixel) %>% 
#   spread(pixel, layer) %>% 
#   rename(plant=ID)


sao_paulo <- read_state(code_state="SP", year=2018)
sao_paulo <- st_transform(sao_paulo, crs = crs_latlon)

# =================================== plot ===================================
breaks <- seq(-1, 1, by = 0.01)
tm_shape(ndvi_rast) +
  tm_raster(midpoint = 0, palette = viridis(length(breaks)), style = "cont", title = "NDVI") +
  tm_shape(sao_paulo) + tm_borders(col = "white") +
  # tm_shape(loc_plant) + tm_bubbles(size=0.04, col = "red") +
  tm_layout(frame = F, between.margin=0) +
  tm_graticules(col="white", lwd=0.5) +
  tm_layout(legend.show=F, legend.outside = T, legend.outside.position="right")

# tmap_save(ndvi_map, filename = "plant.png", dpi = 500)

# =================================== proj em metros (utm) ===================================
crs <- "+proj=utm +zone=22S +datum=GRS80 +units=m +no_defs +towgs84=0,0,0"
ndvi_rast <- projectRaster(ndvi_rast, crs="+proj=utm +zone=22 +south +datum=WGS84 +units=m +no_defs")







# 
# # ponto por ponto (ponto 1)
# crs_m = "+proj=utm +zone=22S +datum=WGS84 +units=m +no_defs +towgs84=0,0,0"
# loc_plant <- st_transform(loc_plant, crs=crs_m)
# loc_plant <- st_buffer(loc_plant, dist=1000)
# loc_plant <- st_transform(loc_plant, crs=crs_latlon)
# 
# ndvi_rast_raio <- crop(ndvi_rast, filter(loc_plant, row_number() == 2))
# # locVals_mtr_p <- getValuesBlock(ndvi_rast_raio, format="matrix", nrows=nrow(ndvi_rast_raio)) # matriz
# # locVals_mtr_p <- getValues(ndvi_rast_raio) # vetor
# 
# # comparando raio esperado e retangulo
# tm_shape(ndvi_rast_raio) + tm_raster(midpoint = NA, palette = viridis(length(breaks)), style = "cont", title="NDVI") +
#   tm_layout(legend.outside = T, legend.outside.position = "right", legend.outside.size = 0.1)
#   # tm_shape(filter(loc_plant_2km, row_number() == 1)) + tm_borders(col="white")
# 
# # fazer lista de matrizes com recortes ao longo do tempo
# 
# setwd("/run/media/wesley/6CD80ADD0368A759/Cepagri/goes_server/ascii")
# files <- str_sub(list.files(), 1, 39)
# patt <- files %>% 
#   str_subset("SP_Bandas_2_3--L1B") %>% 
#   str_sub(1, 10) %>% 
#   unique()
# 
# patt <- c(patt[1], patt[2])
# 
# rm(valsTempo, ndvi_rast, ndvi_rast_raio, ndvi, locVals_mtr_p, loc_plant_1km)
# 
# for(pattern in patt){
#   pHora <- str_subset(files, pattern)
#   # print(pattern)
#   ndvi <- matrix(-10, byrow= TRUE, ncol = 2110, nrow = 1332)
#   
#   for(arq in pHora){
#     c2 <- scan(file = paste(arq, "C02.txt", sep = ""), sep = ",", quiet=T)
#     c2 <- matrix(c2, byrow= TRUE, ncol = 2110, nrow = 1332)
# 
#     c3 <- scan(file = paste(arq, "C03.txt", sep = ""), sep = ",", quiet=T)
#     c3 <- matrix(c3, byrow= TRUE, ncol = 2110, nrow = 1332)
# 
#     ndvi_tmp <- t(c3-c2)/t(c3+c2)
#     ndvi <- pmax(ndvi_tmp, ndvi)
#     # print(paste("ndvi_tmp:", min(ndvi_tmp), ", ", max(ndvi_tmp)))
#     # print(paste("ndvi:", min(ndvi), ", ", max(ndvi)))
#     # rm(c2, c3, ndvi_tmp)
#   }
# 
#   ndvi_rast <- setValues(ndvi_rast, as.vector(ndvi))
#   ndvi_rast <- flip(ndvi_rast, 2)
#   # rm(ndvi)
# 
#   ndvi_rast <- projectRaster(ndvi_rast, 
#                              crs="+proj=utm +zone=22S +datum=WGS84 +units=m +no_defs +ellps=WGS84 +towgs84=0,0,0")
#   loc_plant <- st_transform(loc_plant, crs = crs(ndvi_rast, asText=TRUE))
#   loc_plant_1km <- st_buffer(loc_plant, dis=1000)
#   ndvi_rast_raio <- crop(ndvi_rast, filter(loc_plant_1km, row_number() == 5))
# 
#   locVals_mtr_p <- tibble::enframe(getValues(ndvi_rast_raio)) %>%
#     spread(value = value, key = name)
#   print(locVals_mtr_p)
# 
#   if(exists("valsTempo")) {
#     valsTempo <- bind_rows(valsTempo, locVals_mtr_p)
#     print(paste(str_sub(pattern, 1, 4), "-", str_sub(pattern, 5, 6), "-", str_sub(pattern, 7, 8), 
#                 " ", str_sub(pattern, 9, 10), "h", sep=""))
#   } else {
#       valsTempo <- locVals_mtr_p
#       print("inicio")
#       print(paste(str_sub(pattern, 1, 4), "-", str_sub(pattern, 5, 6), "-", str_sub(pattern, 7, 8), 
#                   " ", str_sub(pattern, 9, 10), "h", sep=""))
#     }
# }
# 
# library(scales)
# 
# valsTempo <- mutate(valsTempo, date=paste(str_sub(patt, 1, 4), "-", str_sub(patt, 5, 6), "-", 
#                                           str_sub(patt, 7, 8), " ", str_sub(patt, 9, 10), ":00:00", sep=""))
# 
# # valsTempo <- mutate(valsTempo, date=paste(str_sub(patt, 1, 4), "-", str_sub(patt, 5, 6), "-", str_sub(patt, 7, 8), sep=""), 
# #                                           time=as.numeric(str_sub(patt, 9, 10)))
# # filter(valsTempo, time >= 8 & time <= ) # valores de ndvi maiores que 1
#   
# valsTempo <- mutate(valsTempo, date=as.POSIXct(date, tx="UTC"))
# # valsTempo <- mutate(valsTempo, date=format(date, tz="Etc/GMT-3",usetz=F))
# valsTempo_plt <- gather(valsTempo, key="pixel", value = "ndvi", -date) %>% 
#   arrange(pixel)
# # valsTempo_plt <- valsTempo_plt %>% 
#   # filter(date >= as.POSIXct("2019-07-19 10:00:00", tx="UTC") & date <= as.POSIXct("2019-08-15 19:00:00", tx="UTC"))
# 
# valsTempo_plt %>% 
#   # filter(ndvi <= 1 & ndvi >= -1) %>% 
#   ggplot() + 
#   geom_line(aes(x=date, y=ndvi, colour=pixel)) + 
#   theme_bw() +
#   theme(axis.text.x = element_text(angle = 90)) +
#   scale_x_datetime(breaks = date_breaks("1 hour")) +
#   scale_y_continuous()
# 
# # Roerink, G. J., Menenti, M. and Verhoef, W., 2000. 
# # Reconstructing cloudfree NDVI composites using Fourier analysis of time series. 
# # International Journal of Remote Sensing, 21 (9), 1911-1917. DOI: 10.1080/014311600209814

