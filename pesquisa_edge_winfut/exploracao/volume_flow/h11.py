import numpy as np, pandas as pd
from es import *
import wf
df = pd.read_pickle('disc.pkl')
F = pd.read_pickle('feat4.pkl')
pd.set_option('display.width',250)
g = F.groupby('day')
key = pd.MultiIndex.from_arrays([F.day.values, F['mod'].values])
def crv_of(col, nd, agg='median'):
    c = F.groupby('day')[col].cumsum()
    piv = F.assign(c=c).pivot_table(index='day', columns='mod', values='c', aggfunc='first')
    r = piv.shift(1).rolling(nd, min_periods=min(3,nd))
    med = (r.median() if agg=='median' else r.mean()).stack()
    return c.values / med.reindex(key).values
nv=0; summ=[]
def run(name, sg):
    global nv
    res = bt_grid(df, sg); nv += len(res)
    r5 = res[(res['T']==500)&(res.S==500)].iloc[0]; r44=res[(res['T']==400)&(res.S==400)].iloc[0]; r3 = res[(res['T']==300)&(res.S==300)].iloc[0]
    summ.append(dict(name=name, n=r5.n, mean_tot=round(res.tot.mean()), frac_pos=round((res.tot>0).mean(),2), best_td=res.td.max(), min_td=res.td.min(),
        td55=r5.td, h1_55=r5.h1, h2_55=r5.h2, td44=r44.td, td33=r3.td))
def rule(T, crv, thr, dirsrc):
    S = F.assign(crv_=crv, ds=dirsrc)
    S = S[(S['mod']==T)].dropna(subset=['crv_'])
    return [(i, int(np.sign(rd)) if cr>=thr else -int(np.sign(rd))) for i,cr,rd in zip(S.index,S.crv_,S.ds) if rd!=0]
base_crv = crv_of('qty', 10)
for T in (30, 31):
    for thr in (0.8, 0.9, 1.1, 1.2):
        run(f'T={T} thr={thr}', rule(T, base_crv, thr, F.ret_day.values))
    for nd in (5, 20):
        run(f'T={T} nd={nd}', rule(T, crv_of('qty', nd), 1.0, F.ret_day.values))
    run(f'T={T} nd=10 mean', rule(T, crv_of('qty', 10, 'mean'), 1.0, F.ret_day.values))
    run(f'T={T} trades-based', rule(T, crv_of('trades', 10), 1.0, F.ret_day.values))
    run(f'T={T} dir=dvwap', rule(T, base_crv, 1.0, F.dvwap.values))
print(pd.DataFrame(summ).to_string())
print('variants', bump(nv))
