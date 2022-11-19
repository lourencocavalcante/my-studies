import time
import subprocess
import os
import gc

gc.enable()

start = time.time()
path_ano = "/mnt/storage/level1b/ano2019/"


g = range(1, 256)
f = []
for i in g:
    f.append(str(i).zfill(3))

dias = list()
for i in f:
    dias.append("dia" + str(i))

incomming = "/ess/data/satellite/goes/grb/level1b/incoming"
processed = "/ess/data/processed"

for d in dias:
    # files = os.listdir(path_ano + d)
    os.system("cp " + path_ano + d + "/OR_ABI-L1b-RadF* " + incomming)
    sp_files = list()
    while len(os.listdir(incomming)) > 0:
        subprocess.call("geosatDPS")
        files_proc = os.listdir(processed)

        for fl in files_proc:
            if fl.endswith("ascii--L1B.C02.txt") or fl.endswith("ascii--L1B.C03.txt") or fl.endswith("ascii--L1B.C06.txt"):
                sp_files.append(fl)

    os.system("tar -czf " + "/home/ess/wesley/" + sp_files[0][0:8] + ".tar.gz" + ' ' + processed + "/*SP_2_3_6_ascii--L1B*.txt")
    os.system("rm /ess/data/satellite/goes/grb/level1b/*.nc /ess/data/processed/*SP_2_3_6_ascii--L1B*")

end = time.time()
print(str((end - start)/60) + " minutos")
