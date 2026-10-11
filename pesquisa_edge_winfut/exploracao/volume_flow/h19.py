import numpy as np, pandas as pd
from es import *
df = pd.read_pickle('disc.pkl'); F = pd.read_pickle('feat4.pkl')
pd.set_option('display.width',250)
tp = (F.high+F.low+F.close)/3
vw = (tp*F.qty).groupby(F.day).sum()/F.qty.groupby(F.day).sum()
F['pvwap'] = F.day.map(lambda d: vw.get(d-1, np.nan))
ok = ((F.time<=165900)&(F['mod']>=5)).values
prevc = F.groupby('day').close.shift(1).values; L = F.pvwap.values
fa = (prevc > L) & (F.low.values <= L); fb = (prevc < L) & (F.high.values >= L)
d = np.where(fa, -1, np.where(fb, 1, 0))
sg = [(i,int(d[i])) for i in np.flatnonzero(ok&(d!=0))]
res = bt_grid(df, sg); print(res.to_string()); print('mean_tot', res.tot.mean(), 'frac', (res.tot>0).mean())
print('variants', bump(len(res)))
