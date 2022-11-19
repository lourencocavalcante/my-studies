source("https://www.dropbox.com/s/xt8bipung6s2897/funcoes.R?dl=1")

sv_points <- function(type, values, file){
  rast <- raster(xmn = -53.4948231956, xmx = -43.9471907179, ymn = -25.4224855885, 
                 ymx = -19.4198207653,  ncols = 2110, nrows = 1332, crs = coord_crs)
  rast <- setValues(rast, as.vector(values))
  rast <- flip(rast, 2)
  
  # loc_vals <- raster::extract(x=rast, y=loc_plant, buffer=1000, df=T) %>%
  loc_vals <- raster::extract(x=rast, y=loc_plant, df=T) %>%
    as_tibble() %>% 
    group_by(ID) %>%
    mutate(pixel=paste0("pixel_", str_pad(seq(1, length(ID), 1), width=2, pad="0", side="left") )) %>% 
    spread(pixel, layer) %>% 
    rename(plant=ID) %>%
    mutate(data = paste0(str_sub(file, 1, 4), "-", str_sub(file, 5, 6), "-", str_sub(file, 7, 8), 
                         ' ', str_sub(file, 9, 10), ":", str_sub(file, 11, 12)),
           index=as.character(type))
  
  if(file.exists("inpe_queimadas.csv")) {
    write_csv(loc_vals, path = "inpe_queimadas.csv", append = TRUE)
  } else {
    write_csv(loc_vals, path = "inpe_queimadas.csv", append = FALSE, col_names = TRUE)
  }
  return()
}

coord_crs <- '+proj=longlat +ellps=WGS84 +towgs84=0,0,0 +no_defs'

municipios <- c("RIBEIRAO PRETO", "JABOTICABAL", "PIRACICABA", "SERTAOZINHO",
                "LIMEIRA", "SAO SIMAO", "AGUDOS", "SAO JOSE DO RIO PRETO")

set.seed(13)
loc_orig <- read_csv("https://www.dropbox.com/s/m9wmu3rppq96k01/Focos_2019-01-01_2019-12-31.csv?dl=1") 
loc_1 <- loc_orig %>% 
  dplyr::filter(riscofogo==1, bioma=="Cerrado") %>%
  dplyr::filter(municipio %in% municipios) %>% 
  tidyr::unite(lat_lon_mun, latitude, longitude, municipio, sep=';') %>% 
  dplyr::mutate(hash = as.character(lapply(lat_lon_mun, digest))) %>% 
  dplyr::distinct(hash, .keep_all=TRUE) %>%
  tidyr::separate(lat_lon_mun, into=c("latitude", "longitude", "municipio"), sep=';') %>% 
  dplyr::filter(!(municipio %in% c("AGUDOS", "RIBEIRAO PRETO", "SERTAOZINHO"))) %>% 
  dplyr::select(-hash) %>% 
  dplyr::mutate(latitude = as.numeric(latitude), longitude = as.numeric(longitude))

loc_2 <- loc_orig %>% 
  dplyr::filter(municipio %in% c("AGUDOS", "RIBEIRAO PRETO", "SERTAOZINHO")) %>% 
  dplyr::group_by(municipio) %>%
  dplyr::sample_n(2, replace = FALSE) 

loc_plant <- dplyr::bind_rows(loc_1, loc_2)

# write_csv(loc_plant, "/home/wesley/Dropbox/IC - Wesley/processamento/inpe_queimadas/focos_filtrados.csv")

loc_plant <- dplyr::select(loc_plant, latitude, longitude) %>%
  sf::st_as_sf(coords = c(2,1), crs=coord_crs)

system("rclone ls remote:goes_bands > drive_filelist.txt")
files_drive <- arrange(read_delim("drive_filelist.txt", delim = ' ', col_names = FALSE), X2)
files_drive <- files_drive$X2

for (f in files_drive){
  system(paste0("rclone copy remote:goes_bands/", f, ' ', "data"))
  system(paste0("tar xzf data/", f, " --strip=3", " --directory data/"), intern = FALSE, wait = TRUE)
  
  files <- list.files("data", pattern = ".txt") %>% 
    str_sub(1, 36) %>% 
    unique()
  
  invisible(mclapply(files, prc, mc.cores = 13))
  
  system("rm data/* && rm drive_filelist.txt")
  # break
}
system("rclone copy /home/cluster/ra188650/proc_imecc remote:proc_imecc")

