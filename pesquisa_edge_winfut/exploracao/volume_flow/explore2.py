import numpy as np, pandas as pd
F = pd.read_pickle('feat.pkl')
ok = (F.time <= 165900) & F['fwd30'].notna() & (F['mod']>=5)
G = F[ok].copy()
half = G.day < 29
feats = ['clv','ats','rv_tod','rt_tod','ats_tod','rng_tod','rv_loc10','rv_loc60','ret1','ret5','ret15','ret30','ret60',
         'press5','press10','press30','press60','sv5','sv10','sv30','sv60','csv_day','cpress_day','dvwap','ret_day']
rows=[]
for f in feats:
    x = G[f]
    r = {}
    for H in ('fwd5','fwd15','fwd30','fwd60'):
        r[H] = x.corr(G[H], method='spearman')
    r['h1_30'] = x[half].corr(G.loc[half,'fwd30'], method='spearman')
    r['h2_30'] = x[~half].corr(G.loc[~half,'fwd30'], method='spearman')
    rows.append(pd.Series(r, name=f))
print(pd.DataFrame(rows).round(4))
