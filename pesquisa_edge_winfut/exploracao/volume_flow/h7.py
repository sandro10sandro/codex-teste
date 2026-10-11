import numpy as np, pandas as pd
from es import *
F = pd.read_pickle('feat2.pkl')
pd.set_option('display.width',250)
for N in (15,30,60):
    F[f'rvN{N}'] = F.rv_tod.groupby(F.day).transform(lambda s: s.rolling(N, min_periods=N).mean())
F.to_pickle('feat3.pkl')
ok = ((F.time <= 165900) & (F['mod']>=15)).values
rows=[]; nv=0
for N in (15,30,60):
    x = np.log(F[f'rvN{N}'].values)
    for c in (0.2, 0.35, 0.5):
        for side in ('both','long','short'):
            d = np.where(x <= -c, 1, np.where(x >= c, -1, 0))
            if side=='long': d = np.where(d==1,1,0)
            if side=='short': d = np.where(d==-1,-1,0)
            sg = [(i,int(d[i])) for i in np.flatnonzero(ok & (d!=0))]
            sg = dedup(sg, F, 30); nv+=1
            r = fwd_study(F, sg)
            if r: rows.append(dict(N=N,c=c,side=side,**r))
out = pd.DataFrame(rows)
print(out[['N','c','side','n','fwd15','fwd30','fwd30_t','fwd60','fwd60_t','L500_500','L500_500_t','L500_500_h1','L500_500_h2','L300_300','L300_300_t']].to_string())
print('variants', bump(nv))
