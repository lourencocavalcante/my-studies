# nohup R CMD BATCH analise.R &

source("https://www.dropbox.com/s/xt8bipung6s2897/funcoes.R?dl=1")

# original <- read_csv("../../IC - dados/dados_analise/inpe_queimadas.csv", n_max = 100)
# plan_n <- max(unique(original$plant))

back <- function(dados, pos){
  # transformada(dados, "ndvi")
  # transformada(dados, "nbr")
  dados %>% 
    # dplyr::filter(plant==i, index==indice) %>% 
    dplyr::select_if(function(x){!all(is.na(x))}) %>% 
    tidyr::separate(data, into = c("data", "hora"), sep = ' ') %>% 
    dplyr::mutate(hora = hms::as_hms(hora)) %>% 
    tidyr::gather(pixel, valor, -c(plant, data, hora, index)) %>% 
    unite("data_hora", c(data, hora), sep = ' ', remove = FALSE) %>% 
    mutate(data_hora = ymd_hms(data_hora)) %>% 
    arrange(data_hora)
}

# setwd("../../IC - dados/tidy_queimadas")

dados <- read_csv_chunked("~/inpe_queimadas.csv",
                          callback = DataFrameCallback$new(back),
                          chunk_size = 1e3)


library(tidyverse)
library(robfilter)

# arquivos queimadas com buffer
arq_queimadas <- list.files("../../IC - dados/tidy_queimadas/com_buffer/", full.names = T)
plant14.ndvi <- read_csv(arq_queimadas[12])
plant14.nbr <- read_csv(arq_queimadas[11])
plant14 <- bind_rows(plant14.ndvi, plant14.nbr)

a <- plant14 %>% 
  filter(pixel == "pixel_01", index == "nbr")

a$diff

ggplot(plant14) + geom_line(aes(x = data_hora, y = med)) + facet_wrap(~pixel + index) + ylim(-1, 1)
# cols <- unique(queima.med$plant_index)
# 
# queima.med <- queima.med %>% 
#   spread(plant_index, pixel_01, drop = FALSE) %>% 
#   setDT() %>% 
#   .[, (cols) := lapply(.SD, filter), 
#     .SDcols = cols]

dados <- dados %>%
  arrange(data_hora) %>% 
  group_by(pixel, plant) %>% 
  mutate(med = filtro_mediana(valor))

ggplot(dados) + 
  geom_line(aes(x = data_hora, y = valor)) + 
  facet_wrap(c("pixel", "plant"))

####################################################################################
# path <- "../../IC - dados/dados_analise/original/"
# path <- "../../IC - dados/dados_analise/queimadas/pontual/brutos/"
# path <- "../../IC - dados/dados_analise/queimadas/com_buffer/"
# 
# nbr_arq <- list.files(path, pattern = "nbr")
# num <- str_extract(nbr_arq, "(\\d)+")
# 
# nbr_arq <- tibble(arq = nbr_arq) %>% 
#   mutate(plant = as.numeric(num)) %>% 
#   arrange(plant)
# 
# ndvi_arq <- list.files(path, pattern = "ndvi_final")
# num <- str_extract(ndvi_arq, "(\\d)+")
# 
# ndvi_arq <- tibble(arq = ndvi_arq) %>% 
#   mutate(plant = num)
# 
# focos <- read_csv("../processamento/inpe_queimadas/focos_filtrados.csv") %>% 
#   mutate(datahora = str_replace_all(datahora, pattern = "/", replacement = "-")) %>% 
#   mutate(datahora = lubridate::as_datetime(datahora))
# 
# for(i in 1:nrow(nbr_arq)){
#   nbr_arq$arq[i]
#   
#   nbr <- read_csv(paste0(path, nbr_arq$arq[i])) %>%
#     gather("metodo", "valor", -c(data_hora, pixel)) %>% 
#     mutate(indice = "nbr")
#   
#   ndvi <- read_csv(paste0(path, ndvi_arq$arq[i])) %>% 
#     gather("metodo", "valor", -c(data_hora, pixel)) %>% 
#     mutate(indice = "ndvi")
#   
#   data <- bind_rows(ndvi, nbr) %>% 
#     filter(metodo == "hants_128") %>% 
#     arrange(data_hora) %>% 
#     mutate(lat = focos[i, ]$latitude, lon = focos[i, ]$longitude, 
#            municipio = focos[i, ]$municipio, data_queima = focos[i, ]$datahora)
#   
#   pl <- ggplot(data) + geom_line(aes(x = data_hora, y = valor, colour = pixel), size = 0.3) +
#     facet_wrap(~indice, nrow = 2) +
#     ylab("Índice") + xlab("Data") +
#     geom_vline(xintercept = focos[i, ]$datahora, col = "black", linetype = "dashed", size = 0.2) +
#     theme_bw()
# 
#   ggsave(plot = pl, paste0(path,
#                            str_remove(nbr_arq$arq[i], pattern = "nbr_final.csv"), "final.png"),
#          width = 10, height = 4, dpi = 700)
# }
# 
# a <- nbr %>% filter(metodo == "mvc") %>% 
#   separate(data_hora, sep = ' ', into = c("data", "hora")) %>% 
#   filter(valor < 1, valor!=-99) %>% group_by(data) %>% 
#   summarise(max_val = max(valor))
# 
# ggplot(arrange(a, data)) + geom_line(aes(x = ymd(data), y = max_val)) + ylim(0.5, 1)
# 
# b <- ndvi %>% filter(metodo == "mvc") %>% 
#   separate(data_hora, sep = ' ', into = c("data", "hora")) %>% 
#   filter(valor < 1, valor!=-99) %>% group_by(data) %>% 
#   summarise(max_val = max(valor))
# 
# ggplot(arrange(b, data)) + geom_line(aes(x = ymd(data), y = max_val)) + ylim(0.5, 1)
# 
# arqs <- list.files("../../IC - dados/tidy_original/")
# 
# for(i in arqs) {
#   data <- read_csv(i)
#   final <- aplica_metod(data)
#   write_csv(final, paste0(str_remove(i, pattern = ".csv"), "_final.csv"))
# }

library(tidyverse)
# library(data.table)
library(robfilter)

focos <- read_csv("../processamento/inpe_queimadas/focos_filtrados.csv") %>% 
  mutate(datahora = str_replace_all(datahora, pattern = "/", replacement = "-")) %>% 
  mutate(datahora = lubridate::as_datetime(datahora)) %>% 
  mutate(plant = 1:16)

queima <- read_csv("../../IC - dados/dados_analise/inpe_queimadas.csv") %>% 
  arrange(data) %>% 
  separate(data, into=c("data", "hora"), sep=' ') %>% 
  # dplyr::filter(index == "ndvi") %>% 
  mutate(hora = lubridate::hms(hora))

# horas_possiveis <- seq(queima$data[1], queima$data[nrow(queima)], by="hour")

# horarios entre 9h e 11h e 13h e 15h
temp1 <- dplyr::filter(queima, hora >= lubridate::hms("12:00:00"), hora <= lubridate::hms("14:00:00"))
temp2 <- dplyr::filter(queima, hora >= lubridate::hms("16:00:00"), hora <= lubridate::hms("18:00:00"))

queima.max <- bind_rows(temp1, temp2) %>% 
  mutate(so.hora = lubridate::hour(hora)) %>% 
  # naniar::replace_with_na(replace = list(pixel_01 >= 1, pixel_01 <= -1)) %>%
  filter(pixel_01 > -1, pixel_01 < 1) %>% 
  group_by(data, so.hora, plant, index) %>% 
  summarise(max = max(pixel_01)) %>% 
  unite("data", c(data, so.hora), sep = ' ') %>% 
  arrange(data) %>% 
  mutate(data = lubridate::ymd_h(data))

rm(temp1, temp2)

# unique(queima.max$plant)

queima.max <- inner_join(queima.max, focos, by = c("plant" = "plant"))
queima.max <- rename(queima.max, "data_queima" = datahora)

queima.max %>% 
  filter(plant == 1) %>% 
  ggplot() + geom_line(aes(x = data, y = max)) + facet_wrap(~index, ncol = 1) + 
  theme_linedraw() + geom_vline(aes(xintercept = data_queima), color = "red") +
  ylab("Índice") + xlab("Data") + ggtitle(municipio)

# TESTE CHANGEPOINT
library(changepoint)

load("/home/wesley/ic/testes com dados de queimadas/queimadas_mediana_livre.RData")

focos <- read_csv("../processamento/inpe_queimadas/focos_filtrados.csv") %>% 
  mutate(datahora = str_replace_all(datahora, pattern = "/", replacement = "-")) %>% 
  mutate(datahora = lubridate::as_datetime(datahora)) %>% 
  mutate(plant = 1:16)

queima.med <- as_tibble(queima.med) %>% 
  mutate(plant = as.numeric(plant)) %>% 
  inner_join(focos, by = c("plant" = "plant")) %>% 
  rename("data_queima" = datahora)

queima1 <- dplyr::filter(queima.med, plant == 9)
plot(queima1$valor, type = "l")
y <- na.omit(queima1$valor)

m.pelt <- cpt.mean(y,  method = "PELT")
plot(m.pelt, type = "l")

mv.pelt <- cpt.meanvar(y, method = "PELT", penalty = "Asymptotic", pen.value = 0.000000000000001)
plot(mv.pelt, type = "l")

v.pelt <- cpt.var(y,  method = "PELT")
plot(v.pelt, type = "l")

# muito lerdo
m.neig <- cpt.mean(y, penalty = "BIC", method = "SegNeigh", Q = 3)
plot(m.neig, type = "l")

m.binseg <- cpt.mean(y, method = "BinSeg")
plot(m.binseg, type = "l")

# rm(temp1, temp2)


queima.max %>% 
  # dplyr::filter(plant == 1) %>% 
  ggplot() + geom_line(aes(x = data, y = max)) +
  geom_vline(xintercept =  lubridate::ymd_h("2019-10-17 03"), col = "red") + 
  facet_wrap(~plant) + 
  ylim(-0.5, 1)



nbr <- separate(queima, data, into=c("data", "hora"), sep=' ') %>% 
  dplyr::filter(index == "nbr") %>% 
  mutate(hora = lubridate::hms(hora))

# filtro de mediana
queima.med <- rbind(temp1, temp2) %>% 
  unite("data_hora", c(data, hora), sep = ' ')

d <- lubridate::ymd_hms(queima.med$data_hora)

queima.med <- mutate(queima.med, data_hora = d, plant = as.character(plant)) %>% 
  dplyr::filter(pixel_01 < 1, pixel_01 > -1) %>%
  arrange(data_hora) %>% 
  unite("plant_index", c(plant, index), sep = '-')

filter <- function(y) return(adore.filter(y)[["y"]])

cols <- unique(queima.med$plant_index)

queima.med$plant_index <- factor(queima.med$plant_index)

queima.med <- queima.med %>% 
  spread(plant_index, pixel_01, drop = FALSE) %>% 
  setDT() %>% 
  .[, (cols) := lapply(.SD, filter), 
                         .SDcols = cols]

queima.med <- gather(queima.med, "plant_index", "valor", -data_hora) %>% 
  separate(plant_index, into=c("plant", "index"), sep='-') %>% 
  arrange(data_hora, as.numeric(plant))

data.queim <- focos$datahora
i <- 6

queima.med %>% 
  dplyr::filter(plant == i) %>% 
  ggplot() + geom_line(aes(x = data_hora, y = valor)) + 
  geom_vline(xintercept =  lubridate::ymd_hms(data.queim[i]), col = "red") + 
  facet_wrap(~index, nrow = 2) + 
  # ylim(-1, 1) + 
  theme_bw()


queimadas <- read_csv("~/inpe_queimadas.csv")



library(signal)

?sgolayfilt





