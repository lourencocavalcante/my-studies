library(readr)
library(dplyr)
library(raster)
library(stringr)

c02 <- read_csv("/run/media/wesley/7516e311-0543-49f0-a5b4-64733f1ba546/G16.SP_Bandas_2_3--L1B/201907141440G16.SP_Bandas_2_3--L1B.pic.C02.txt", col_names = F)
c03 <- read_csv("/run/media/wesley/7516e311-0543-49f0-a5b4-64733f1ba546/G16.SP_Bandas_2_3--L1B/201907141440G16.SP_Bandas_2_3--L1B.pic.C03.txt", col_names = F)

path <- '/run/media/wesley/7516e311-0543-49f0-a5b4-64733f1ba546/G16.SP_Bandas_2_3--L1B/'
path <- '/run/media/wesley/6CD80ADD0368A759/Cepagri/goes_server/ascii/'
files <- list.files(path)

files <- as_tibble(files) %>% 
    filter(str_detect(value, c("C03", "C02"))) %>%
    mutate(value = str_c(substr(value, 1, 25), date=str_c(substr(value, 1, 4), substr(value, 5, 6), substr(value, 7, 8), sep="-"),
           hour=substr(value, 9, 10),
           min=substr(value, 11, 12)) %>% 
    group_by(hour)
View(files)
