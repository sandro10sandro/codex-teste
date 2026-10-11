import numpy as np, pandas as pd
F = pd.read_pickle('feat2.pkl')
for N in (15,30,60):
    F[f'rvN{N}'] = F.rv_tod.groupby(F.day).transform(lambda s: s.rolling(N, min_periods=N).mean())
ok = (F.time <= 165900) & (F['mod']>=30) & F.fwd60.notna()
G = F[ok].copy()
for N in (15,30,60):
    G['rq'] = pd.qcut(G[f'ret{N}'], 5, labels=False)
    G['vq'] = pd.qcut(G[f'rvN{N}'], 3, labels=False)
    for H in ('fwd30','L500_500'):
        t = G.pivot_table(index='rq', columns='vq', values=H, aggfunc='mean').round(1)
        t1 = G[G.day<29].pivot_table(index='rq', columns='vq', values=H, aggfunc='mean').round(1)
        t2 = G[G.day>=29].pivot_table(index='rq', columns='vq', values=H, aggfunc='mean').round(1)
        print(f'N={N} {H}  all | h1 | h2'); print(pd.concat([t,t1,t2],axis=1).to_string())
