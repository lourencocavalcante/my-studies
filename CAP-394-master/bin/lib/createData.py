#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 19 16:36:40 2019

@author: hneto
"""

import pandas as pd
import os
from lib.read_files import readData
from lib.tRelation import tRelation
import numpy as np
#import xarray as xr


## Varriable to get LAT LON

fisrtRead = readData(20140103)
lat,lon = fisrtRead[1],fisrtRead[2]

path = '../data/radar/'

def createData(day,time,clusters,frames):
    
    ##Static Radar Coordinates Value for Topological relation
    radar = (-3.148556, -59.992000)

    if isinstance(clusters,pd.DataFrame):

        FAM1 = pd.DataFrame(columns=['YEAR','MONTH','DAY','HOUR','MINUTE',
                                     'N_Cluster','ID_CLUS','LAT','LON','IND_X','IND_Y',
                                     'T_RELATION','RAIN_FALL','DBz'])


        LAT_ = (lat[clusters['x1'].astype(int),clusters['y1'].astype(int)])
        LON_ = (lon[clusters['x1'].astype(int),clusters['y1'].astype(int)])
        N_CLUST = len(clusters['cluster'].unique())

        rfall = []
        rlation = []
        
        for i,row in clusters.iterrows():
            rfall.append(frames[row['x1'].astype(int)][row['y1'].astype(int)])
            r = tRelation((LAT_[i],LON_[i]),radar)
            rlation.append(r)
            

        FAM1['IND_X'], FAM1['IND_Y'] = clusters['x1'],clusters['y1']
        FAM1['LAT'],FAM1['LON'] = LAT_,LON_
        FAM1['N_Cluster'] = N_CLUST
        FAM1['ID_CLUS'] = clusters['cluster']
        FAM1['RAIN_FALL'] = rfall
        FAM1['T_RELATION'] = rlation
        FAM1['DBz'] =  10 * np.log10(200*FAM1['RAIN_FALL']**1.6)
        FAM1['YEAR'] = str(sorted(os.listdir(path+str(day)))[time])[16:20]
        FAM1['MONTH'] = str(sorted(os.listdir(path+str(day)))[time])[20:22]
        FAM1['DAY'] = str(sorted(os.listdir(path+str(day)))[time])[22:24]
        FAM1['HOUR'] = str(sorted(os.listdir(path+str(day)))[time])[25:27]
        FAM1['MINUTE'] = str(sorted(os.listdir(path+str(day)))[time])[27:29]
       
    else:
        return None

    return FAM1