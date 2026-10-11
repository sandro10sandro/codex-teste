import numpy as np, pandas as pd
F = pd.read_pickle('feat2.pkl')
g = F.groupby('day')
F['fwd120'] = g.close.shift(-120).values - g.open.shift(-1).values
for T in (15, 30, 45, 60, 90, 120):
    S = F[F['mod']==T]
    out=[]
    for f in ['cpress_day','csv_day','ret_day','dvwap']:
        for H in ['fwd30','fwd60','fwd120','L500_500']:
            c = S[f].corr(S[H], method='spearman')
            out.append(f'{f[:5]}/{H[:6]}={c:+.2f}')
    print(T, ' '.join(out))
