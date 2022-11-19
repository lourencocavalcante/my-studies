library(tidyverse)
library(robfilter)

original <- read_csv("../../../IC - dados/tidy_queimadas/pontual/plant_14_nbr.csv")

serie <- original$valor

# proporcao de valores faltantes
sum(is.na(serie)) / length(serie)

# Procedure for robust online extraction of low frequency components (the signal) from a univariatetime 
# series by a moving window technique with adaptive window width selection (ADaptive OnlineREpeated median FILTER)
med.adore1 <- adore.filter(serie, width.search = "geometric", min.width = 35)
med.adore2 <- adore.filter(serie, width.search = "linear", min.width = 35)
med.adore3 <- adore.filter(serie, width.search = "binary", min.width = 35)
med.adore51 <- adore.filter(serie, width.search = "geometric", min.width = 51)

med.adore1.livre <- adore.filter(serie, width.search = "geometric")
med.adore2.livre <- adore.filter(serie, width.search = "linear")
med.adore3.livre <- adore.filter(serie, width.search = "binary")

# Filtering procedure based on a weighted version of Siegel’s (1982) repeated median (RM) and amoving time window 
# for robust extraction of low frequency components (the signal) in the presenceof outliers and shifts. 
# One of several weight functions can be chosen to weight the observations ineach time window.

# med.wrm <- wrm.filter(serie, width = 35, weight.type = 0)
med.wrm <- wrm.filter(serie, width = 51, weight.type = 1) # mais recomendado

save.image("mediana.RData")

# nohup R CMD BATCH testes_filtro_mediana.R &

################################

load("mediana.RData")

plot(med.adore1, ylim = c(-1.5, 1.5))
plot(med.adore2, ylim = c(-1.5, 1.5))
plot(med.wrm, ylim = c(-1.5, 1.5))

y = med.adore1[["level"]]
y = med.adore2[["level"]]
y = med.wrm[["level"]]

med.frame <- mutate(original, med.adore1 = med.adore1[["level"]],
                    med.wrm = med.wrm[["level"]], 
                    med.adore2 = med.adore2[["level"]], 
                    med.adore51 = med.adore51[["level"]])

ggplot(med.frame) + 
  # geom_line(aes(x = data_hora, y = valor)) +
  geom_line(aes(x = data_hora, y = med.adore1)) +
  # geom_line(aes(x = data_hora, y = med.adore2)) +
  # geom_line(aes(x = data_hora, y = med.adore51)) +
  ylim(-1, 1)

# Savitzky-Golay filtro

library(signal)
sg <- sgolayfilt(na.omit(serie))
med.frame <- mutate(med.frame, sg = sg)


ggplot() + geom_line(aes(x = 1:length(sg), y = sg)) + ylim(-1, 1)

m.pelt <- cpt.mean(sg, method = "PELT")
plot(m.pelt)

mv.pelt <- cpt.meanvar(sg, method = "PELT", penalty = "Asymptotic", pen.value = 1e-15)
plot(mv.pelt, ylim = c(-1,1))

mv.pelt <- cpt.meanvar(sg, method = "PELT", penalty = "Asymptotic", pen.value = 0.000000000000001)
plot(mv.pelt, type = "l")


# VALORES MAXIMOS
library(lubridate)
max_hora <- original %>% 
  mutate(hora = lubridate::hour(hora)) %>% 
  group_by(data, hora, index) %>% 
  summarise(v_max = max(valor)) %>% 
  ungroup() %>% 
  mutate(hora = as.character(hora), data = as.character(data)) %>% 
  unite("data_h", c(data, hora), sep = ' ') %>% 
  mutate(data_h = lubridate::ymd_h(data_h), adore = adore.filter(v_max, min.width = 11)[["level"]])

ggplot(max_hora) + 
  # geom_line(aes(x = data_h, y = v_max)) +
  geom_line(aes(x = data_h, y = adore)) +
  ylim(-1, 1)

# testes com pontos de mudança

library(changepoint)
m.pelt <- cpt.mean(med.frame$med.wrm, method = "PELT")
plot(m.pelt)

mv.pelt <- cpt.meanvar(med.frame$med.wrm, method = "PELT", penalty = "Asymptotic", pen.value = 1e-15)
plot(mv.pelt)

mv.pelt <- cpt.meanvar(med.frame$med.wrm, method = "PELT", penalty = "Asymptotic", pen.value = 0.000000000000001)
plot(mv.pelt, type = "l")







