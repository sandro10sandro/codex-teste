import numpy as np, pandas as pd
from es import *
df = pd.read_pickle('disc.pkl'); F = pd.read_pickle('feat4.pkl')
pd.set_option('display.width',250)
g = F.groupby('day')
F['dlo_prev'] = g.low.transform(lambda s: s.cummin().shift(1)); F['dhi_prev'] = g.high.transform(lambda s: s.cummax().shift(1))
ok = ((F.time<=165900)&(F['mod']>=30)).values
nl = (F.low < F.dlo_prev).values; nh = (F.high > F.dhi_prev).values
rows=[]; nv=0
for k in (1.5, 2.0, 3.0):
    for clvt in (0.0, 0.3):
        for mode in ('fade','follow'):
            L = nl & (F.rv_tod.values>=k) & (F.clv.values>=clvt if mode=='fade' else F.clv.values<=-clvt)
            H = nh & (F.rv_tod.values>=k) & (F.clv.values<=-clvt if mode=='fade' else F.clv.values>=clvt)
            d = np.where(L, 1 if mode=='fade' else -1, np.where(H, -1 if mode=='fade' else 1, 0))
            sg = [(i,int(d[i])) for i in np.flatnonzero(ok&(d!=0))]
            sg = dedup(sg, F, 20); nv+=1
            r = fwd_study(F, sg)
            if r: rows.append(dict(k=k,clv=clvt,mode=mode,**r))
out=pd.DataFrame(rows)
print(out[['k','clv','mode','n','fwd15','fwd30','fwd30_t','fwd60','L500_500','L500_500_t','L500_500_h1','L500_500_h2','L300_300','L300_300_t']].to_string())
print('variants', bump(nv))
