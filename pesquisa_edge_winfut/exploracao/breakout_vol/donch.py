from feats import *
df = get_df()
day = df['day'].values; mod = df['mod'].values
h = df['high'].values; l = df['low'].values; c = df['close'].values
rng = h - l
atr_long = pd.Series(rng).rolling(120, min_periods=60).mean().values  # crosses days, past only
res = []
for L in (15, 30, 60):
    hh = roll_max_prev(h, day, L); ll = roll_min_prev(l, day, L)
    width = (hh - ll) / atr_long
    for sq in (None, 'low'):   # squeeze filter: width in bottom tercile of its expanding distribution? use fixed relative threshold
        up = c > hh; dn = c < ll
        up, dn = edge_events(up, dn, day)
        if sq == 'low':
            thr = {15: 3.5, 30: 5.0, 60: 7.0}[L]
            # print quantiles once
            q = np.nanquantile(width, [0.2, 0.33, 0.5])
            print(L, 'width quantiles', q.round(2))
            up &= width < q[1]; dn &= width < q[1]
        for mode in ('mom', 'fade'):
            sg = [(i, 1 if mode == 'mom' else -1) for i in np.flatnonzero(up)] + [(i, -1 if mode == 'mom' else 1) for i in np.flatnonzero(dn)]
            g = grid(df, sg); g['L'] = L; g['sq'] = str(sq); g['mode'] = mode
            res.append(g)
R = pd.concat(res)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
print(R.groupby(['L','sq','mode']).agg(n=('n','mean'),tot_mean=('total','mean'),tot_max=('total','max'),tmax=('t','max'),npos=('total',lambda x:(x>0).sum())))
print(R[R.apply(passes, axis=1)])
print('variants', VARIANTS[0])
R.to_csv('donch.csv', index=False)
