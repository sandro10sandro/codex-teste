from feats import *
df = get_df()
day = df['day'].values; mod = df['mod'].values
h = df['high'].values; l = df['low'].values; c = df['close'].values
# running day high/low up to previous bar
hp = pd.Series(h).groupby(day).transform(lambda v: v.cummax().shift(1)).values
lp = pd.Series(l).groupby(day).transform(lambda v: v.cummin().shift(1)).values
res = []
for tmin in (30, 60, 120):
    for trig in ('close', 'touch'):
        up = (c > hp) if trig == 'close' else (h > hp)
        dn = (c < lp) if trig == 'close' else (l < lp)
        up &= mod >= tmin; dn &= mod >= tmin
        for mode in ('mom', 'fade'):
            sg = [(i, 1 if mode == 'mom' else -1) for i in np.flatnonzero(up)] + [(i, -1 if mode == 'mom' else 1) for i in np.flatnonzero(dn)]
            g = grid(df, sg); g['tmin'] = tmin; g['trig'] = trig; g['mode'] = mode
            res.append(g)
R = pd.concat(res)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
print(R.groupby(['tmin','trig','mode']).agg(n=('n','mean'),tot_mean=('total','mean'),tot_max=('total','max'),tmax=('t','max'),npos=('total',lambda x:(x>0).sum())))
print(R[R.apply(passes, axis=1)])
print('variants', VARIANTS[0])
R.to_csv('hod.csv', index=False)
