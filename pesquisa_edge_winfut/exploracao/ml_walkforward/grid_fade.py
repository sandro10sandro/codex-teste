from win import *
from wf import backtest
rd = F['r_day'].values
def fade_sig(a, b, K):
    m = valid & (modv >= a) & (modv < b) & (np.abs(rd) > K)
    return [(i, -1 if rd[i] > 0 else 1) for i in np.flatnonzero(m)]
rows = []
for a in (0, 15, 30):
    for b in (60, 90, 120):
        for K in (20, 30, 40, 50):
            sig = fade_sig(a, b, K)
            for T in (200, 300, 400, 500):
                for S in (200, 300, 400, 500):
                    tr, st = backtest(df, sig, T, S, 'base')
                    tro = tr[tr.date.isin(OOS_DATES)]
                    rows.append(dict(a=a, b=b, K=K, T=T, S=S, n=st['n'], tot=st['total'], t=st['t_daily'], h1=st['first_half_total'], h2=st['second_half_total'],
                                     oos_tot=tro.pnl.sum()))
R = pd.DataFrame(rows); R.to_csv('grid_fade.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
print('mean t over TS grid'); print(R.pivot_table(index=['a','b'], columns='K', values='t', aggfunc='mean').round(2))
print('frac TS combos with h1>0 & h2>0'); print(R.assign(ok=(R.h1>0)&(R.h2>0)).pivot_table(index=['a','b'], columns='K', values='ok', aggfunc='mean').round(2))
print('n (500/500)'); print(R[(R['T']==500)&(R.S==500)].pivot_table(index=['a','b'], columns='K', values='n'))
for (T,S) in [(400,400),(500,500),(300,300),(200,500)]:
    print(T,S,'t'); print(R[(R['T']==T)&(R.S==S)].pivot_table(index=['a','b'], columns='K', values='t').round(2))
