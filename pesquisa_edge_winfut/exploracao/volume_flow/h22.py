import numpy as np, pandas as pd
from es import *
df = pd.read_pickle('disc.pkl'); F = pd.read_pickle('feat4.pkl')
pd.set_option('display.width',250)
nv=0; summ=[]
for step, start in ((60, 30), (30, 30)):
    for c in (0.0, 0.03, 0.06):
        m = F['mod'].values; cp = F.cpress_day.values
        ev = (m >= start) & ((m - start) % step == 0) & (np.abs(cp) > c) & (F.time.values <= 165900)
        sg = [(i, int(-np.sign(cp[i]))) for i in np.flatnonzero(ev)]
        res = bt_grid(df, sg); nv += len(res)
        r5 = res[(res['T']==500)&(res.S==500)].iloc[0]
        summ.append(dict(step=step, c=c, n5=r5.n, mean_tot=round(res.tot.mean()), frac_pos=round((res.tot>0).mean(),2), best_td=res.td.max(), td55=r5.td, h1=r5.h1, h2=r5.h2))
print(pd.DataFrame(summ).to_string())
print('variants', bump(nv))
