import numpy as np, pandas as pd
from es import *
import wf
df = pd.read_pickle('disc.pkl')
F = pd.read_pickle('feat3.pkl')
pd.set_option('display.width',250)
g = F.groupby('day')
F['cqty'] = g.qty.cumsum()
piv = F.pivot_table(index='day', columns='mod', values='cqty', aggfunc='first')
med = piv.shift(1).rolling(10, min_periods=3).median().stack()
key = pd.MultiIndex.from_arrays([F.day.values, F['mod'].values])
F['crv'] = F.cqty.values / med.reindex(key).values
F.to_pickle('feat4.pkl')
print(F[F['mod']==30].crv.describe())
nv=0
summ=[]
for T in (10, 15, 20, 25, 30, 35, 40, 45, 60, 90):
    S = F[(F['mod']==T)].dropna(subset=['crv'])
    sg = []
    for i, cr, rd in zip(S.index, S.crv, S.ret_day):
        if rd == 0: continue
        d = int(np.sign(rd)) if cr >= 1.0 else -int(np.sign(rd))
        sg.append((i, d))
    res = bt_grid(df, sg); nv += len(res)
    summ.append(dict(T=T, mean_tot=round(res.tot.mean()), frac_pos=round((res.tot>0).mean(),2), best_td=res.td.max(),
                     td_500=res[(res['T']==500)&(res.S==500)].td.iloc[0], tot_500=res[(res['T']==500)&(res.S==500)].tot.iloc[0],
                     h1_500=res[(res['T']==500)&(res.S==500)].h1.iloc[0], h2_500=res[(res['T']==500)&(res.S==500)].h2.iloc[0],
                     td_300=res[(res['T']==300)&(res.S==300)].td.iloc[0]))
    if T in (25,30,35): print(T); print(res.to_string())
print(pd.DataFrame(summ).to_string())
print('variants', bump(nv))
