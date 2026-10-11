import numpy as np, pandas as pd
from es import *
df = pd.read_pickle('disc.pkl'); F = pd.read_pickle('feat4.pkl')
pd.set_option('display.width',250)
pc = F.groupby('day').close.last()
F['gap'] = F.groupby('day').open.transform('first') - F.day.map(lambda d: pc.get(d-1, np.nan))
nv=0; summ=[]
for T in (0, 4):
    S = F[(F['mod']==T)].dropna(subset=['crv','gap'])
    S = S[S.gap!=0]
    for name, sg in (('switch', [(i, int(np.sign(gp)) if cr>=1 else -int(np.sign(gp))) for i,cr,gp in zip(S.index,S.crv,S.gap)]),
                     ('fade_gap', [(i, -int(np.sign(gp))) for i,gp in zip(S.index,S.gap)]),
                     ('follow_gap', [(i, int(np.sign(gp))) for i,gp in zip(S.index,S.gap)])):
        res = bt_grid(df, sg); nv+=len(res)
        r5 = res[(res['T']==500)&(res.S==500)].iloc[0]
        summ.append(dict(T=T, name=name, n=r5.n, mean_tot=round(res.tot.mean()), frac_pos=round((res.tot>0).mean(),2), best_td=res.td.max(), td55=r5.td, h1=r5.h1, h2=r5.h2))
print(pd.DataFrame(summ).to_string())
print('variants', bump(nv))
