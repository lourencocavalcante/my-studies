##################################### leitura de funções #####################################
# source("https://www.dropbox.com/s/xt8bipung6s2897/funcoes.R?dl=1")
source("../funcoes.R")

# focos de queimada de interesse
focos <- readr::read_csv("../processamento/inpe_queimadas/focos_filtrados.csv") %>% 
  dplyr::mutate(datahora = str_replace_all(datahora, pattern = "/", replacement = "-")) %>% 
  dplyr::mutate(datahora = lubridate::as_datetime(datahora), plant = 1:16)

# # séries anuais de pontos de queimada e vizinhos
# dado <- read_csv("../../IC - dados/tidy_queimadas/queimadas_buffer.csv", n_max = 70000) %>% dplyr::select(-med)
# 
# # unir focos com dados de queima
# dado <- inner_join(dado, focos, by = c("plant"="plant"))
# dado <- rename(dado, "data_queima" = datahora)

##################################### composição de valor máximo ##################################### 
# # horarios entre 9h e 11h e 13h e 15h
# temp1 <- dplyr::filter(dado, hora >= lubridate::hms("12:00:00"), hora <= lubridate::hms("14:00:00"))
# temp2 <- dplyr::filter(dado, hora >= lubridate::hms("16:00:00"), hora <= lubridate::hms("18:00:00"))
# 
# # valor máximo por hora
# queima_max <- dplyr::bind_rows(temp1, temp2) %>% 
#   dplyr::mutate(hora = lubridate::hour(hora)) %>%
#   # naniar::replace_with_na(replace = list(pixel_01 >= 1, pixel_01 <= -1)) %>% # trocar valores fora de (-1, 1)
#   dplyr::filter(valor > -1, valor < 1) %>% 
#   dplyr::group_by(data, hora, pixel, plant, index, municipio) %>% 
#   dplyr::summarise(max = max(valor)) %>% 
#   tidyr::unite("data", c(data, hora), sep = ' ') %>% 
#   dplyr::mutate(data = lubridate::ymd_h(data)) %>% 
#   dplyr::arrange(data)
# 
# rm(dado, temp1, temp2)
# 
# save.image("/home/cluster/ra188650/home_imecc/public_html/queimadas.RData") # cluster
# load("queimadas.RData") # máquina local

queima_max %>% 
  dplyr::filter(plant == 15, index == "nbr") %>% 
  ggplot2::ggplot() +
  ggplot2::geom_line(aes(x = data, y = max)) +
  ggplot2::facet_wrap(~pixel) +
  # facet_grid(rows = vars(plant))+
  ggplot2::ylab("Índice") + ggplot2::xlab("Data") +
  ggplot2::theme_linedraw()

##################################### filtro de mediana #####################################

library(robfilter)

filter <- function(vec) return(robfilter::adore.filter(vec, min.width = 5, sign.level=0.001)[["level"]])

med <- dado %>%
  dplyr::group_by(plant, pixel, index) %>%
  dplyr::mutate(med_adore = filter(valor)) %>%
  dplyr::mutate(comb = coalesce(med_adore, valor)) # reutilizar 5 primeiras observações

# rm(dado, temp1, temp2, queima_max)

med.adore1 <- adore.filter(med$valor, width.search = "geometric", min.width = 5, sign.level = 0.001)
length(med.adore1)
nrow(med)

save.image("/home/cluster/ra188650/home_imecc/public_html/mediana.RData") # cluster

load("mediana.RData")
plot(med.adore1, ylim = c(-2, 2))

read_med <- function(input, pos){
  input %>% 
    # dplyr::rename(mediana = comb) %>% 
    dplyr::filter(plant == plant_n, pixel == px)
}

plant_n <- 15
px <- "pixel_05"
med <- read_csv_chunked("~/mediana.csv",
                        DataFrameCallback$new(read_med),
                        col_types = cols_only(plant = col_guess(), data_hora = col_guess(),
                                      index = col_guess(), pixel = col_guess(),
                                      data_queima = col_guess(), municipio = col_guess(),
                                      comb = col_guess()),
                        chunk_size = 1e7)


# COLOCAR RESULTADOS PONTUAIS?

####### TESTES #######
# med <- dplyr::mutate(med, med.adore1 = med.adore1[["level"]])
# 
# ggplot(med) + geom_line(aes(x = data_hora, y = med.adore1))
# 
# med.adore2 <- adore.filter(med$valor, width.search = "linear", min.width = 5)
# plot(med.adore2)
# 
# med.adore3 <- adore.filter(med$valor, width.search = "binary", min.width = 5)
# plot(med.adore3)
# 
# med.adore51 <- adore.filter(med$valor, width.search = "geometric", min.width = 5)
# plot(med.adore51)
# 
# med.adore1.livre <- adore.filter(med$valor, width.search = "geometric")
# plot(med.adore1.livre)
# 
# med.adore2.livre <- adore.filter(med$valor, width.search = "linear")
# plot(med.adore2.livre)
# 
# med.adore3.livre <- adore.filter(med$valor, width.search = "binary")
# plot(med.adore3.livre)

# TODOS OS MÉTODOS PARECEM DAR O MESMO RESULTADO

################################ pontos de mudança com valores máximos ################################

library(changepoint)

# load("/home/cluster/ra188650/home_imecc/public_html/queimadas.Rdata") # cluster
load("queimadas.RData") # local

ponto <- dplyr::filter(queima_max, plant == 14, index == "nbr", pixel == "pixel_01")
mv_max <- cpt.meanvar(ponto$max, method = "BinSeg", Q = 5)
plot(mv_max)

# mv_bic <- cpt.meanvar(ponto$max, method = "BinSeg", penalty = "BIC", Q = 5)
# plot(mv_bic)

# save.image("/home/cluster/ra188650/home_imecc/public_html/pontos.RData") # cluster

############################### pontos de mudança com filtro de mediana ###############################

load("~/mediana.RData")

med %>% 
  ggplot() + geom_line(aes(x=data_hora, y = comb)) + facet_wrap(~index, ncol=1)

med_cpt = med %>% dplyr::filter(index == "nbr")
mv_med_nbr <- cpt.meanvar(med_cpt$comb, method = "BinSeg", Q = 5)
plot(mv_med_nbr)

pt <- tibble(x = mv_med_nbr@cpts, y = mv_med_nbr@param.est[["mean"]])
ymap <- c()
media <- mv_med_nbr@param.est[["mean"]]
xpos <- mv_med_nbr@cpts
for(i in 1:length(xpos)) ymap <- c(ymap, rep(media[i], seg.len(mv_med_nbr)[i]))
med_cpt <- dplyr::mutate(med_cpt, cpt_y=ymap)

ggplot(med_cpt) + 
  geom_line(aes(x=data_hora, y=comb)) + 
  geom_line(aes(x=data_hora, y=cpt_y, group=as.factor(cpt_y)), col='red')
  
med_cpt = med %>% dplyr::filter(index == "ndvi")
mv_med_ndvi <- cpt.meanvar(med_cpt$comb, method = "BinSeg", Q = 5)
plot(mv_med_ndvi)

med_cpt <- cpt.mean(med_cpt$comb, method = "BinSeg", Q = 5)
plot(m_med_ndvi)



