import numpy as np, pandas as pd
from es import *
df = pd.read_pickle('disc.pkl'); F = pd.read_pickle('feat4.pkl')
pd.set_option('display.width',250)
nv=0
for T in (120, 121):
    S = F[(F['mod']==T)].dropna(subset=['crv'])
    sg = [(i, int(np.sign(rd)) if cr>=1 else -int(np.sign(rd))) for i,cr,rd in zip(S.index,S.crv,S.ret_day) if rd!=0]
    res = bt_grid(df, sg); nv+=len(res)
    print(T, 'mean_tot', round(res.tot.mean()), 'frac_pos', round((res.tot>0).mean(),2)); print(res[res['T']==res.S].to_string())
print('variants', bump(nv))
