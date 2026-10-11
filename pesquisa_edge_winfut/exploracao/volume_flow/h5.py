import numpy as np, pandas as pd
from es import *
import wf
df = pd.read_pickle('disc.pkl')
F = pd.read_pickle('feat2.pkl')
pd.set_option('display.width',250)
nv=0
for f in ['cpress_day','ret_day']:
  for T in (30, 45, 60):
    idx = np.flatnonzero(F['mod'].values==T)
    sg = [(i, int(-np.sign(F[f].values[i]))) for i in idx if F[f].values[i]!=0]
    res = bt_grid(df, sg); nv += len(res)
    print(f, T); print(res.sort_values('tot',ascending=False).head(6).to_string())
    print('  mean tot over grid', round(res.tot.mean(),1), ' frac>0', round((res.tot>0).mean(),2))
print('variants', bump(nv))
