from feats import *
df = get_df()
day = df['day'].values; mod = df['mod'].values
o = df['open'].values; h = df['high'].values; l = df['low'].values; c = df['close'].values
res = []
VARIANTS[0] = 0
def add(sg, **kw):
    g = grid(df, sg)
    for k, v in kw.items(): g[k] = v
    res.append(g)
hp = pd.Series(h).groupby(day).transform(lambda v: v.cummax().shift(1)).values
lp = pd.Series(l).groupby(day).transform(lambda v: v.cummin().shift(1)).values
# late-day first new HOD/LOD after time tmin (first event per day only)
for tmin in (330, 390):
    for mode in ('mom', 'fade'):
        sg = []
        for s, e in zip(*day_groups(df)):
            for i in range(s, e):
                if mod[i] < tmin: continue
                if c[i] > hp[i]: sg.append((i, 1 if mode == 'mom' else -1)); break
                if c[i] < lp[i]: sg.append((i, -1 if mode == 'mom' else 1)); break
        add(sg, fam='late_hodlod', p=tmin, mode=mode)
# turtle soup: bar makes new L-bar low (low < prior L-bar min) but closes back above that prior min -> long (and mirror)
for L in (30, 60, 120):
    hh = roll_max_prev(h, day, L); ll = roll_min_prev(l, day, L)
    up = (l < ll) & (c > ll) & (mod >= 30)    # failed breakdown -> long
    dn = (h > hh) & (c < hh) & (mod >= 30)
    sg = [(i, 1) for i in np.flatnonzero(up)] + [(i, -1) for i in np.flatnonzero(dn)]
    add(sg, fam='turtle_soup', p=L, mode='fade')
R = pd.concat(res)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
print(R.groupby(['fam', 'p', 'mode']).agg(n=('n','mean'),tot_mean=('total','mean'),tot_min=('total','min'),tot_max=('total','max'),tmax=('t','max'),npos=('total',lambda x:(x>0).sum())))
print(R[R.apply(passes, axis=1)].to_string())
print('variants', VARIANTS[0])
