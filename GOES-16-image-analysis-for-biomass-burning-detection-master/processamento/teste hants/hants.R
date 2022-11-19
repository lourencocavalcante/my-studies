library(geoTS)
library(tidyverse)
library(lubridate)

load("vetores.RData")

# faltantes
faltantes <- vetores %>% filter_all(any_vars(is.na(.)))

y <- as.vector(drop_na(vetores)$`1`)

# Filtro mediana (suavização)
movingMedian <- function(y, m = 7){
  n <- length(y)
  y.hat <- numeric(n)
  y <- c(rep(median(y), m), y)
  for(i in 1:n){
    y.hat[i] <- median(y[i:(i-m) + m], na.rm = TRUE)
  }
  return(y.hat)
}

filterY <- movingMedian(y, 10)

# plot(y, type = "l", ylim  = c(-1,1))
# lines(filterY, col = "Red")

# plot(filterY, type = "l", ylim  = c(-1,1), col = "Red")

# Filtro usando o Hants (remover obs faltantes)
# w <- as.numeric(na.omit(y))

y <- d$`1`
y <- na.omit(y)
fitted <- haRmonics(y, method = "hants", ts = 1:length(y),
                    lenBasePeriod = length(y), numFreq = 32, HiLo = "Lo", 
                    low = -0.7, high = 0.7, fitErrorTol = 0.2, 
                    degreeOverDeter=10, delta=0.1)

fit <- fitted[["fitted"]]
# plot(fit, type = "l", ylim = c(-1,1))
# abline(h=0.35, lty = 2, col = "red")

# load("vetores.RData")

vet <- vetores %>%
  mutate(data=as.character(data), hora=as.character(hora)) %>%
  unite("hora", data:hora, sep=' ') %>%
  mutate(hora=as.POSIXct(strptime(hora, "%Y.%m.%d %H:%M:%S"), tz='UTC'), fit_hants_1=fit, series_1=filterY) %>% 
  select(hora, `1`, fit_hants_1, series_1) %>% gather("ajuste", "valor", `1`:series_1)
  # mutate(hora=as_datetime(hora)) %>%
  # mutate(hora_uncls=unclass(hora))

time_breaks <- vetores$hora %>%
  str_sub(1, 20) %>%
  unique()
 

vet %>% 
  # filter(hora > as.POSIXct("2019-06-15 00:00:00", tz = "UTC") & 
           # hora < as.POSIXct("2019-06-16 00:00:00", tz = "UTC")) %>% 
  ggplot(aes(x=as_datetime(hora), y=valor)) +
  geom_line() +
  facet_wrap(~ajuste) +
  # scale_x_continuous(name="Data", breaks=seq(1, length(time_breaks), 1), labels = time_breaks) +
  scale_x_datetime(name = "Data", date_breaks = "1 day") +
  theme_bw() +
  theme(axis.text.x = element_text(angle = 90)) +
  ylab("NDVI") + xlab("Data/hora") + ylim(-0.5, 0.7)

filter(vet, ajuste=="fit_hants_1") %>% 
ggplot(aes(x=as_datetime(hora), y=valor)) +
  geom_line() +
  theme_bw() +
  theme(axis.text.x = element_text(angle = 90))


a <- filter(vet, ajuste=="fit_hants_1")

b <- filter(vet, ajuste=="1")

# b <- seq(as.POSIXct("2019-06-07 14:40:00 UTC"),
    # as.POSIXct("2019-08-24 17:50:00 UTC"), by = "10 min")

plot(a$hora, na.omit(a$valor), type="l", ylim=c(-1,1))
lines(b$hora, na.omit(b$valor), type="l", col="red")

# 
# 
# vet <- vet %>%
#   mutate(data=as.character(data), hora=as.character(hora)) %>%
#   unite("hora", data:hora, sep=' ') %>%
#   mutate(hora=as.POSIXct(strptime(hora, "%Y.%m.%d %H:%M:%S"), tz='UTC'), fit_hants_1=fit, series_1=filterY)
# 
# ggplot(vet, aes(x=seq(1, 1612, 1), y=fit_hants_1)) +
#   geom_line() +
#   # facet_wrap(~ajuste) +
#   # scale_x_continuous(name="Data", breaks=seq(1, length(time_breaks), 1), labels = time_breaks) +
#   theme_bw() +
#   theme(axis.text.x = element_text(angle = 90)) +
#   ylab("NDVI")

plot(vetores$`1`, type="l", ylab = "NDVI", xlab = "")
lines(filterY, lwd=1.5, type="l", col="#00FDFF")
lines(fit, lwd=2, type="l", col="red")

