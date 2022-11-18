import pandas as pd
import numpy as np

def pre_processing(time1):
    
    te = pd.DataFrame()    
    dx ,dy = [],[]
    
    for i in range(241):
        for j in range(241):
            if not np.isnan(time1[i][j]) and time1[i][j] > 21.8:
                dx.append(i)
                dy.append(j)

    dim = len(dx)
    
    # Check dimension
    if dim > 4:   
        for x in range(dim):
            dx.append(np.float32('nan'))
            dy.append(np.float32('nan'))

        matrix = np.ndarray(shape=(dim, 2), dtype='float32')
        pt = pd.DataFrame(columns=['x1','y1'])
    
        for x in range(dim):
            matrix[x] = (dx[x], dy[x])
            pt['x1'] = matrix[:,0]
            pt['y1'] = matrix[:,1]

        te = pt[['x1','y1']]
        
    return te
