library(tidyverse)
library(lubridate)
library(geoTS)
library(data.table)
library(raster)
library(geobr)
library(sf)
library(parallel)
library(rgdal)
library(digest)
library(gridExtra)
# library(kableExtra)
# library(tmap)
library(viridis)
library(changepoint)

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

# SEPARA POR PLANTACOES E LIDA COM DADOS FALTANTES PARA O HANTS
arrumadinha <- function(dados, indice){
  for(i in 1:plan_n){
    dados_1 <- dados %>% 
      dplyr::filter(plant==i, index==indice) %>%
      dplyr::select_if(function(x){!all(is.na(x))}) %>% 
      tidyr::separate(data, into = c("data", "hora"), sep = ' ') %>% 
      dplyr::mutate(hora = hms::as_hms(hora))  
    
    if(indice == "ndvi"){
      temp_1 <- dados_1 %>% 
        dplyr::filter(hora >= hms::as_hms("08:00:00"), hora <= hms::as_hms("18:00:00"))
      
      temp_2 <- dados_1 %>% 
        dplyr::filter(hora < hms::as_hms("08:00:00")) %>% 
        dplyr::mutate_at(vars(matches("pixel")), function(x){rep(999, length(x))})
      
      temp_3 <- dados_1 %>% 
        dplyr::filter(hora > hms::as_hms("18:00:00")) %>% 
        dplyr::mutate_at(vars(matches("pixel")), function(x){rep(999, length(x))})
      
      # nrow(temp_1) + nrow(temp_2) + nrow(temp_3)
      # sort(unique(as.character(temp_1$hora)))
      # sort(unique(as.character(temp_2$hora)))
      # sort(unique(as.character(temp_3$hora)))
      
      temp <- bind_rows(temp_1, temp_2, temp_3) %>% 
        tidyr::unite("data", c(data, hora), sep= ' ') %>%
        dplyr::arrange(data)
    } else {temp <- dados_1}
    
    temp[is.na(temp)] <- 999
    
    if(file.exists(paste0("plant_", as.character(i), '_', indice, ".csv"))) {
      readr::write_csv(temp, path = paste0("plant_", as.character(i), '_', indice, ".csv"), append = TRUE)
    } else {
      readr::write_csv(temp, path = paste0("plant_", as.character(i), '_', indice, ".csv"), append = FALSE)
    }
  }
}

# SEPARA POR INDICE E DEIXA TIDY COM DATA E HORA
transformada <- function(dados, indice){
  for(i in 1:plan_n){
    dados1 <- dados %>% 
      dplyr::filter(plant==i, index==indice) %>%
      dplyr::select_if(function(x){!all(is.na(x))}) %>% 
      tidyr::separate(data, into = c("data", "hora"), sep = ' ') %>% 
      dplyr::mutate(hora = hms::as_hms(hora)) %>% 
      tidyr::gather(pixel, valor, -c(plant, data, hora, index)) %>% 
      unite("data_hora", c(data, hora), sep = ' ', remove = FALSE) %>% 
      mutate(data_hora = ymd_hms(data_hora)) %>% 
      arrange(data_hora)
  
    if(file.exists(paste0("plant_", as.character(i), '_', indice, ".csv"))) {
      readr::write_csv(dados1, path = paste0("plant_", as.character(i), '_', indice, ".csv"), append = TRUE)
    } else {
      readr::write_csv(dados1, path = paste0("plant_", as.character(i), '_', indice, ".csv"), append = FALSE)
    }
  }
}

# APLICA HANTS EM UM VETOR
hants <- function(vec, freq){
  fit <- geoTS::haRmonics(vec, method = "hants", ts = 1:length(vec),
                   lenBasePeriod = length(vec), numFreq = freq, HiLo = "Lo", 
                   low = -1, high = 1, fitErrorTol = 0.05, 
                   degreeOverDeter=10, delta=0.1)[["fitted"]]
  return(fit)
}

# PASSA HANTS EM VARIOS CSVs EM FILES
pass_hants <- function(files){
  for(i in files){
    # print(i)
    
    temp <- readr::read_csv(i, n_max = 5)
    cols <- colnames(temp) %>% 
      str_subset("pixel")
    
    # temp <- readr::read_csv(i) %>% 
    #   dplyr::mutate_at(vars(match("pixel")), hants)
    # 
    # readr::write_csv(temp, paste0(str_remove(i, pattern = ".csv"), "_HANTS.csv"))
    
    readr::read_csv(i, n_max = 5000) %>%
    data.table::setDT() %>%
    .[, (cols) := lapply(.SD, hants), .SDcols = cols] %>%
    tibble::as_tibble() %>% 
    readr::write_csv(paste0(str_remove(i, pattern = ".csv"), "_HANTS.csv"))
  }
  return()
}

# CHECK DATA FALTANTE, ENTRADA DADOS ORIG
check_data <- function(dataset, dta1='2019-01-01 00:00:00', dta2='2019-12-31 23:50:00'){
  data_check <- dataset
  data_check <- unique(data_check$data_hora)
  data_check <- ymd_hms(data_check)
  data_check <- sort(data_check)
  data_seq <- seq(ymd_hms(dta1),ymd_hms(dta2), by = '10 min')
  data_falta <- unique(data_seq[! data_seq %in% data_check])
  
  tib <- tibble(d = data_falta) %>% 
    separate(d, into = c("data", "hora"), sep = ' ') %>% 
    distinct(data)

  return(tib$data)
}

# PLOTA DOIS GRAFICOS DE NBR E NDVI
ts_plot <- function(ndvi, nbr, valor_min, valor_max, valor){
  valor_min <- min(c(ndvi$hants_32, nbr$hants_32))
  valor_max <- max(c(ndvi$hants_32, nbr$hants_32))
  # valor_min <- -0.5
  # valor_max <- 1
    
  nbr_plot <- ggplot(nbr) + geom_line(aes(x=data_hora, y=valor, colour=pixel), size = 0.5) +
    ylim(c(valor_min, valor_max)) +
    theme_bw() +
    theme(legend.position = "none") +
    guides(color = guide_legend(ncol=2)) + 
    ylab("NBR") +
    xlab("")
  
  ndvi_plot <- ggplot(ndvi) + geom_line(aes(x=data_hora, y=valor, colour=pixel), size = 0.5) +
    ylim(c(valor_min, valor_max)) +
    theme_bw() +
    guides(color = guide_legend(ncol=2)) + 
    ylab("NDVI") +
    theme(legend.position = "bottom", legend.box = "vertical",
          legend.direction = "horizontal", legend.title = element_blank()) +
    guides(colour = guide_legend(nrow = 2))

  final_plot <- grid.arrange(nbr_plot, ndvi_plot, padding=0)
  return(final_plot)
}

# valor maximo de uma em uma hora
MVC <- function(dataset, pixels){
  todas_datas <- tibble(data = seq(ymd_h('2019-01-01 00'), 
                                   ymd_h('2019-12-31 23'), 
                                   by = '1 hour'))
  res <- tibble()
  
  for(px in pixels){
    temp <- dataset %>% 
      filter(pixel == px) %>%
      separate(hora, into = c("hora", "m", "s"), sep = ":") %>%
      mutate(fill = "00:00") %>% 
      unite("data_hora", data, hora, sep = ' ') %>% 
      unite("data_hora", data_hora, fill, sep = ':') %>% 
      mutate(data_hora = lubridate::ymd_hms(data_hora, tz = "UTC")) %>% 
      full_join(todas_datas, by = c("data_hora"="data")) %>%
      dplyr::mutate(mvc = replace_na(valor, -99)) %>% 
      # filter(data == "2019-05-01", h == 15, pixel == "pixel_01") %>% 
      group_by(data_hora, pixel) %>% 
      summarise(mvc = max(mvc)) %>% 
      ungroup() %>% 
      mutate(pixel = px) %>% 
      arrange(data_hora)
    res <- bind_rows(res, temp)
  }
  # pixels <- unique(dataset$pixel)
  # res <- tibble()
  
    # filter(pixel == "pixel_01") %>% # aplicar a todos os pixels
    # mutate(fill = "00:00") %>% 
    # unite("data_hora", data, hora, sep = ' ', remove = FALSE) %>% 
    # unite("data_hora", data_hora, fill, sep = ':') %>% 
    # mutate(data_hora = lubridate::ymd_hms(data_hora, tz = "UTC"))

    # mutate(pixel = "pixel_01") %>% 
    # separate(data_hora, into = c("data", "hora"), sep = ' ', remove = FALSE) %>% 
    # mutate(data = lubridate::ymd(data), hora = hms::as_hms(hora)) %>% 
    # arrange(data_hora)
  
  # talvez usar outro join
  # trocar valores faltantes
  return(res)
}


# aplica os metodos MVC e HANTS (freq 32, 64, 128) em um dataset 
aplica_metod <- function(dataset){
  pixels <- unique(dataset$pixel)
  dt <- MVC(dataset, pixels)
  final <- tibble()
  
  for(i in pixels){
    temp <- dt %>% 
      dplyr::filter(pixel == i) %>% 
      dplyr::arrange(data_hora)
    
    vec <- temp$mvc
    vec_32 <- hants(vec, 32)
    vec_64 <- hants(vec, 64)
    vec_128 <- hants(vec, 128)
    
    temp <- dplyr::mutate(temp, 
                   hants_32 = vec_32, 
                   hants_64 = vec_64,
                   hants_128 = vec_128)
    
    final <- dplyr::bind_rows(final, temp)
  }
  
  final <- dplyr::arrange(final, data_hora)
  return(final)
}


plot_cpt <- function(cpt_obj, cpt_frame){
  x = c(0, cpt_obj@cpts)
  xend = x[2:length(x)]
  x = x[1:(length(x)-1)]
  y = cpt_obj@param.est$mean
  
  segmentos <- tibble(x=x, xend=xend, y=y) %>% 
    mutate(x = x+1) %>% 
    group_by(x, xend, y) %>%
    expand(count = x:xend) %>% 
    dplyr::select(-count)
  
  cpt_frame <- bind_cols(cpt_frame, segmentos) %>% 
    group_by(x, xend) %>% 
    mutate(x_data = data[1], xend_data = data[n()])
  
  indice <- unique(cpt_frame$index)
  indice <- str_to_upper(indice)
  
  plot <- ggplot(cpt_frame) + 
    geom_line(aes(x = data, y = valor), size=0.3) +
    geom_segment(aes(x = x_data, xend = xend_data, y=y, yend=y), col="red", size=0.5) +
    ylab(indice) + xlab("Data") + 
    theme_bw() +
    theme(axis.text = element_text(size = 8), 
          plot.margin = margin(0, 0.3, 0, 0, "cm"), 
          axis.title = element_text(size = 10))
  
  return(list(plot, cpt_frame))
}


plot_locs <- function(local){
  cpt_frame.nbr <- med %>% 
    dplyr::filter(index=="nbr", municipio==local) %>% 
    dplyr::mutate(valor=comb, data=data_hora)
  
  cpt_nbr <- changepoint::cpt.meanvar(cpt_frame.nbr$valor, method="BinSeg", Q=5)
  a <- plot_cpt(cpt_nbr, cpt_frame.nbr)[[1]] + 
    geom_vline(xintercept=cpt_frame.nbr$data_queima, linetype="dashed", col="#d48300")
  
  
  cpt_frame.ndvi <- med %>% 
    dplyr::filter(index=="ndvi", municipio==local) %>% 
    dplyr::mutate(valor=comb, data=data_hora)
  
  cpt_ndvi <- changepoint::cpt.meanvar(cpt_frame.ndvi$valor, method="BinSeg", Q=5)
  b <- plot_cpt(cpt_ndvi, cpt_frame.ndvi)[[1]] +
    geom_vline(xintercept=cpt_frame.ndvi$data_queima, linetype="dashed", col="#d48300")
  
  plot <- gridExtra::grid.arrange(grobs=list(b, a), ncol=2, top=local)
  return(plot)
}







