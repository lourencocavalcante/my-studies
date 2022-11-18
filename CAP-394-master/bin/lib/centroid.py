# -*- coding: utf-8 -*-

import pandas as pd

def centroidData(clus):
    if isinstance(clus,pd.DataFrame):
        centroid = pd.DataFrame()
        for i in range(clus['N_Cluster'].max()):
            ct = clus.loc[clus['ID_CLUS'] == i ]
            ct = ct.loc[ct['RAIN_FALL'] == ct['RAIN_FALL'].max()]
            centroid = centroid.append(ct)
    else:
        return None
    return centroid