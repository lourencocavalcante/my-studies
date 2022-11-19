import os, fnmatch

# os.chdir("/media/wesleysatelis/6CD80ADD0368A759/G16.SP_Bandas_2_3--L1B/")
os.chdir("/ess/data/processed")
# os.chdir("/run/media/wesley/6CD80ADD0368A759/G16.SP_Bandas_2_3--L1B/")
listOfFiles = os.listdir('.')
pattern = "*SP_Bandas_2_3--L1B.pic"
os.system("mkdir /home/ess/Desktop/goes_netcdf/")
i = 0
for entry in listOfFiles:  
    if fnmatch.fnmatch(entry, pattern):
		# NETCDF
        os.system("pic2netcdf -i " + entry + " -o /home/ess/Desktop/goes_netcdf/" + entry + " -v")
        # ASCII
        os.system("pic2ascii -i " + entry + " -o /home/ess/Desktop/goes_ascii/" + entry)
        i += 1
    if i == 10:
        break
