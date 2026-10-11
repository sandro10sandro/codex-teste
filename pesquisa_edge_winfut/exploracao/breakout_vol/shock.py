from feats import *
df = get_df()
day = df['day'].values; mod = df['mod'].values
o = df['open'].values; h = df['high'].values; l = df['low'].values; c = df['close'].values
rng = h - l
atr = pd.Series(rng).shift(1).rolling(60, min_periods=30).mean().values
body = c - o
res = []
# shock bar: range > k*ATR and close in top/bottom 30% of bar, direction of body
pos = np.where(rng > 0, (c - l) / np.where(rng > 0, rng, 1), 0.5)
for k in (2.0, 3.0, 4.0):
    big = rng > k * atr
    up = big & (pos > 0.7) & (body > 0) & (mod >= 5)
    dn = big & (pos < 0.3) & (body < 0) & (mod >= 5)
    for mode in ('mom', 'fade'):
        sg = [(i, 1 if mode == 'mom' else -1) for i in np.flatnonzero(up)] + [(i, -1 if mode == 'mom' else 1) for i in np.flatnonzero(dn)]
        g = grid(df, sg); g['fam'] = 'shock'; g['k'] = k; g['mode'] = mode
        res.append(g)
# multi-bar move: close - close[m] > k * ATR*sqrt(m)
for m in (5, 15):
    mv = c - pd.Series(c).groupby(day).shift(m).values
    for k in (2.0, 3.0):
        up = mv > k * atr * np.sqrt(m); dn = mv < -k * atr * np.sqrt(m)
        up, dn = edge_events(up, dn, day)
        for mode in ('mom', 'fade'):
            sg = [(i, 1 if mode == 'mom' else -1) for i in np.flatnonzero(up)] + [(i, -1 if mode == 'mom' else 1) for i in np.flatnonzero(dn)]
            g = grid(df, sg); g['fam'] = f'move{m}'; g['k'] = k; g['mode'] = mode
            res.append(g)
R = pd.concat(res)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
print(R.groupby(['fam','k','mode']).agg(n=('n','mean'),tot_mean=('total','mean'),tot_max=('total','max'),tmax=('t','max'),npos=('total',lambda x:(x>0).sum())))
print(R[R.apply(passes, axis=1)])
print('variants', VARIANTS[0])
R.to_csv('shock.csv', index=False)
