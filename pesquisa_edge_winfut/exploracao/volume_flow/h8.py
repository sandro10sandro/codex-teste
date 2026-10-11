import numpy as np, pandas as pd
from es import *
import wf
df = pd.read_pickle('disc.pkl')
F = pd.read_pickle('feat3.pkl')
pd.set_option('display.width',250)
g = F.groupby('day')
F['cqty'] = g.qty.cumsum()
F['cqty_tod'] = tod_like = None
# cumulative qty since open relative to prior 10 days' cumulative qty at same minute
piv = F.pivot_table(index='day', columns='mod', values='cqty', aggfunc='first')
med = piv.shift(1).rolling(10, min_periods=3).median().stack()
key = pd.MultiIndex.from_arrays([F.day.values, F['mod'].values])
F['crv'] = F.cqty.values / med.reindex(key).values
nv=0; rows=[]
for T in (15, 30, 60):
    S = F[F['mod']==T].dropna(subset=['crv'])
    lv = np.log(S.crv.values); rd = np.sign(S.ret_day.values)
    for H in ('fwd60','L500_500'):
        y = S[H].values if H.startswith('fwd') else np.where(True, S['L500_500'].values, 0)
        # signed outcome of 'follow' = rd*y (for L500 use L if rd>0 else S)
        fol = np.where(rd>0, S['L500_500'].values, S['S500_500'].values) if H=='L500_500' else rd*S[H].values
        hi = lv > np.median(lv)
        rows.append(dict(T=T,H=H, follow_hivol=round(np.nanmean(fol[hi]),1), follow_lovol=round(np.nanmean(fol[~hi]),1),
                         rho=round(pd.Series(lv).corr(pd.Series(fol), method='spearman'),3), n=len(S)))
        nv+=1
print(pd.DataFrame(rows))
print('variants', bump(nv))
