import sys; sys.path.insert(0,'.')
from base import *
import time
df=get_df()
res={}
for cost in ('base','stress'):
    for T in (200,300,400,500):
        for S in (200,300,400,500):
            t0=time.time()
            o=outcomes(df,T,S,cost)
            res[(T,S,cost)]={d:(o[d][0].astype(np.float32),o[d][1].astype(np.int32),o[d][2].astype(np.int8)) for d in (1,-1)}
            print(cost,T,S,round(time.time()-t0,1),flush=True)
pickle.dump(res,open('outcomes.pkl','wb'))
