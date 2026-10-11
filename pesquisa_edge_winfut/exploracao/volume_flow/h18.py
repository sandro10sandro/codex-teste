import numpy as np, pandas as pd
from es import *
df = pd.read_pickle('disc.pkl'); F = pd.read_pickle('feat4.pkl')
pd.set_option('display.width',250)
# prior-day POC and VWAP (in adjusted pts; adjustment ~constant day to day)
tp = (F.high+F.low+F.close)/3
pocs={}; vw={}
for d, gdf in F.groupby('day'):
    tk = gdf.tick.iloc[0]*4
    b = np.round(tp[gdf.index]/tk)*tk
    s = gdf.qty.groupby(b.values).sum()
    pocs[d] = s.idxmax(); vw[d] = (tp[gdf.index]*gdf.qty).sum()/gdf.qty.sum()
F['ppoc'] = F.day.map(lambda d: pocs.get(d-1, np.nan)); F['pvwap'] = F.day.map(lambda d: vw.get(d-1, np.nan))
ok = ((F.time<=165900)&(F['mod']>=5)).values
rows=[]; nv=0
for lvl in ('ppoc','pvwap'):
    L = F[lvl].values
    prevc = F.groupby('day').close.shift(1).values
    # touch from above: previous close above level, this bar low <= level
    fa = (prevc > L) & (F.low.values <= L); fb = (prevc < L) & (F.high.values >= L)
    for mode in ('fade','follow'):
        d = np.where(fa, 1 if mode=='fade' else -1, np.where(fb, -1 if mode=='fade' else 1, 0))
        sg = [(i,int(d[i])) for i in np.flatnonzero(ok&(d!=0))]
        sg = dedup(sg, F, 30); nv+=1
        r = fwd_study(F, sg)
        if r: rows.append(dict(lvl=lvl, mode=mode, **r))
        # first touch of day only
        first = []; seen=set()
        for i,dd in sg:
            if F.day.values[i] in seen: continue
            seen.add(F.day.values[i]); first.append((i,dd))
        r = fwd_study(F, first); nv+=1
        if r: rows.append(dict(lvl=lvl+'_first', mode=mode, **r))
out=pd.DataFrame(rows)
print(out[['lvl','mode','n','fwd15','fwd30','fwd30_t','fwd60','L500_500','L500_500_t','L500_500_h1','L500_500_h2','L300_300','L300_300_t']].to_string())
print('variants', bump(nv))
