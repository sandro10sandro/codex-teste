from common import *
import time
df = get()
OUT = {}
t0=time.time()
for cost in ('base','zero','stress'):
    for T in (200,300,400,500):
        for S in (200,300,400,500):
            o = wf.outcomes(df, T, S, cost)
            OUT[(cost,T,S)] = {d:(o[d][0].copy(), o[d][1].copy(), o[d][2].copy()) for d in (1,-1)}
    print(cost, time.time()-t0, flush=True)
pickle.dump(OUT, open('outc.pkl','wb'))
