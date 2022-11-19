library(tidyverse)
library(sf)

library(raster)
# library(tidyverse)
library(geobr)
# library(sf)
library(parallel)
library(rgdal)
# library(viridis)
# library(tmap)

sv_points <- function(type, values, file){
  rast <- raster(xmn = -53.4948231956, xmx = -43.9471907179, ymn = -25.4224855885, 
                 ymx = -19.4198207653,  ncols = 2110, nrows = 1332, crs = coord_crs)
  rast <- setValues(rast, as.vector(values))
  rast <- flip(rast, 2)
  
  loc_vals <- raster::extract(x=rast, y=loc_plant, buffer=500, df=T) %>% 
    as_tibble() %>% 
    group_by(ID) %>% 
    mutate(pixel=paste0("pixel_", str_pad(seq(1, length(ID), 1), width=2, pad="0", side="left") )) %>% 
    arrange(pixel) %>% 
    spread(pixel, layer) %>% 
    rename(plant=ID) %>%
    mutate(data = paste0(str_sub(file, 1, 4), "-", str_sub(file, 5, 6), "-", str_sub(file, 7, 8), 
                         ' ', str_sub(file, 9, 10), ":", str_sub(file, 11, 12)),
           index=as.character(type))
  
  if(file.exists("inpe_sp.csv")) {
    write_csv(loc_vals, path = "inpe_sp.csv", append = TRUE)
  } else {
    write_csv(loc_vals, path = "inpe_sp.csv", append = FALSE, col_names = TRUE)
  }
  return()
}

prc <- function(arq){
  c2 <- scan(file = paste0("data/", arq, "C02.txt"), sep = ",", quiet = TRUE)
  c2 <- matrix(c2, byrow= TRUE, ncol = 2110, nrow = 1332)
  
  c3 <- scan(file = paste0("data/", arq, "C03.txt"), sep = ",", quiet = TRUE)
  c3 <- matrix(c3, byrow= TRUE, ncol = 2110, nrow = 1332)
  
  c6 <- scan(file = paste0("data/", arq, "C06.txt"), sep = ",", quiet = TRUE)
  c6 <- matrix(c6, byrow= TRUE, ncol = 2110, nrow = 1332)
  
  ndvi <- t(c3-c2)/t(c3+c2)
  nbr <- t(c3-c6)/t(c3+c6)
  rm(c2, c3, c6)
  
  sv_points(type = "ndvi", values = ndvi, file = arq)
  sv_points(type = "nbr", values = nbr, file = arq)
  return()
}

coord_crs <- '+proj=longlat +ellps=WGS84 +towgs84=0,0,0 +no_defs'

# set.seed(13)
# loc_plant <- read.table("https://www.dropbox.com/s/2nuwlw59i22wlrg/sp_12.txt?dl=1") %>% 
#   sample_n(20) %>% 
#   st_as_sf(coords = c(2,1), crs=coord_crs)

# inpe queimadas
loc_plant <- queim %>% 
  filter(bioma == "Cerrado") %>% 
  select(latitude, longitude) %>% 
  st_as_sf(coords = c(2,1), crs=coord_crs)

system("rclone ls remote:goes_bands > drive_filelist.txt")
files_drive <- arrange(read_delim("drive_filelist.txt", delim = ' ', col_names = FALSE), X2)
files_drive <- files_drive$X2

for (f in files_drive){
  system(paste0("rclone copy remote:goes_bands/", f, ' ', "data"))
  system(paste0("tar xzf data/", f, " --strip=3", " --directory data/"), intern = FALSE, wait = TRUE)
  
  files <- list.files("data", pattern = ".txt") %>% 
    str_sub(1, 36) %>% 
    unique()
  
  invisible(mclapply(files, prc, mc.cores = 10))
  
  system("rm data/*")
  # break
}
system("rclone copy /home/cluster/ra188650/proc_imecc remote:proc_imecc && rm drive_filelist.txt")

