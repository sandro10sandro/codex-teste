from orb import orb_signals
from fw import *
df = get_df()
for N in (15, 30):
    sg = orb_signals(df, N, 'fade', True)
    for t, s in [(300, 300), (500, 500), (200, 500), (300, 500)]:
        tr, st = backtest(df, sg, t, s, 'base')
        rb = random_baseline(df, tr, t, s, 'base', n_iter=1000)
        print(N, t, s, {k: st[k] for k in ('n','total','avg','win_rate','t_daily','first_half_total','second_half_total','long_total','short_total')}, 'p', rb['p_value'])
    tr, st = backtest(df, sg, 500, 500, 'base')
    tr['hour'] = tr['time'] // 10000 * 100 + (tr['time'] // 100 % 100) // 30 * 30
    print(tr.groupby('hour')['pnl'].agg(['count', 'sum', 'mean']).round(0).T)
    # nth trade of day
    tr['k'] = tr.groupby('date').cumcount()
    print(tr.groupby('k')['pnl'].agg(['count', 'sum', 'mean']).round(0).T)
    # monthly
    tr['mon'] = tr['date'] // 100
    print(tr.groupby('mon')['pnl'].agg(['count', 'sum', 'mean']).round(0).T)
