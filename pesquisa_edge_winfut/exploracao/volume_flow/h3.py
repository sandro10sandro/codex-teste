import numpy as np, pandas as pd
F = pd.read_pickle('feat2.pkl')
ok = (F.time <= 165900) & (F['mod']>=5) & F.fwd60.notna()
G = F[ok].copy()
G['hr'] = G['mod']//60
for f in ['cpress_day','csv_day','press60','dvwap']:
    print(f, G.groupby('hr').apply(lambda x: round(x[f].corr(x.fwd60, method='spearman'),3)).to_dict())
# day-level sampling: one obs per day per hour at minute 0 of each hour -> independent-ish
S = G[G['mod']%60==0]
for f in ['cpress_day','csv_day','ret_day','dvwap']:
    c = S[f].corr(S.fwd60, method='spearman'); n=len(S)
    print(f, 'hourly sample n', n, 'rho', round(c,3), 't~', round(c*np.sqrt(n-2)/np.sqrt(1-c*c),2),
          'h1', round(S[S.day<29][f].corr(S[S.day<29].fwd60, method='spearman'),3), 'h2', round(S[S.day>=29][f].corr(S[S.day>=29].fwd60, method='spearman'),3))
# components of CLV: decompose cpress into upper wick vs lower wick
