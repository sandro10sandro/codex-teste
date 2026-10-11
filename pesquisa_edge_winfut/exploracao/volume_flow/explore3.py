import numpy as np, pandas as pd
F = pd.read_pickle('feat.pkl')
ok = (F.time <= 165900) & F['fwd30'].notna() & (F['mod']>=5)
G = F[ok].copy()
G['half'] = (G.day >= 29).astype(int)
print(G[['cpress_day','ret_day','csv_day','dvwap','press60']].corr(method='spearman').round(3))
for f in ['cpress_day','csv_day','press60']:
    G['q'] = pd.qcut(G[f], 10, labels=False)
    t = G.groupby(['q'])[['fwd30','fwd60','L500_500','S500_500']].mean().round(1)
    t['h1_L500'] = G[G.half==0].groupby('q').L500_500.mean().round(1)
    t['h2_L500'] = G[G.half==1].groupby('q').L500_500.mean().round(1)
    t['ndays'] = G.groupby('q').day.nunique()
    t['lo'] = G.groupby('q')[f].min().round(3)
    print(f); print(t)
