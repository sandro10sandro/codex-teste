import numpy as np, pandas as pd
from es import bump
F = pd.read_pickle('feat4.pkl')
g = F.groupby('day')
F['eod'] = g.close.transform('last') - g.open.shift(-1).values
nv=0
for T in (449, 469, 479):
    S = F[F['mod']==T].copy()
    for f in ('ret30','ret60','ret_day','press30','cpress_day','dvwap','rvN30'):
        x = S[f]; y = S.eod
        c = x.corr(y, method='spearman'); nv+=1
        c1 = x[S.day<29].corr(y[S.day<29], method='spearman'); c2 = x[S.day>=29].corr(y[S.day>=29], method='spearman')
        print(T, f, round(c,3), round(c1,3), round(c2,3))
    # volume-conditioned: sign(ret30)*eod by rv
    hi = S.rvN30 >= 1
    print(T, 'follow ret30 hivol', (np.sign(S.ret30)*S.eod)[hi].mean().round(1), 'lovol', (np.sign(S.ret30)*S.eod)[~hi].mean().round(1)); nv+=2
print('variants', bump(nv))
