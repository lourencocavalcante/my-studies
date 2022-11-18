# -*- coding: utf-8 -*-

from sklearn.cluster import MeanShift, estimate_bandwidth
#import numpy as np
#import pandas as pd

def clust(time1):    #11.53:

    
    te = time1
    
    if len(te) < 2:
        return None
    
    bandwidth = estimate_bandwidth(te, quantile=0.9)
    
    if bandwidth > 0:
        ms = MeanShift(bandwidth=5, bin_seeding=None, cluster_all=True, min_bin_freq=1,
    n_jobs=None, seeds=None)
    else:
        ms = MeanShift(bandwidth=10, bin_seeding=None, cluster_all=True, min_bin_freq=1,
    n_jobs=None, seeds=None)

    ms.fit(te)
    labels = ms.labels_
#    cluster_centers = ms.cluster_centers_
#    n_clusters_ = len(np.unique(labels))
        
#     colors = 10*['r.','g.','b.','c.','k.','y.','m.']
#     for i in range(len(te)):
#            #print(te['x1'][i])
#         plt.plot(te['x1'][i], te['y1'][i], colors[labels[i]], markersize = 10)
#         plt.title('Estimated number of clusters: %d' % n_clusters_)

#     kmeans = KMeans(n_clusters=8).fit(te)
#     labels = kmeans.labels_
#     cluster_centers = kmeans.cluster_centers_
#     n_clusters_ = len(np.unique(labels))

    te['cluster']=labels

    
    return te