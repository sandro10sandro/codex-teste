from feats import *
df = get_df()
day = df['day'].values; mod = df['mod'].values
o = df['open'].values; h = df['high'].values; l = df['low'].values; c = df['close'].values; q = df['qty'].values
res = []
def add(sg, **kw):
    g = grid(df, sg)
    for k, v in kw.items(): g[k] = v
    res.append(g)

# 1. prior-day high / low: first cross per day, mom/fade
dd = df.groupby('day').agg(H=('high', 'max'), L=('low', 'min'))
pH = dd['H'].shift(1).values[day]; pL = dd['L'].shift(1).values[day]
for mode in ('mom', 'fade'):
    sg = []
    for s, e in zip(*day_groups(df)):
        if np.isnan(pH[s]): continue
        du = dn = False
        for i in range(s + 1, e):
            if not du and c[i] > pH[i] and c[i - 1] <= pH[i]:
                sg.append((i, 1 if mode == 'mom' else -1)); du = True
            if not dn and c[i] < pL[i] and c[i - 1] >= pL[i]:
                sg.append((i, -1 if mode == 'mom' else 1)); dn = True
    add(sg, fam='prevday', p=0, mode=mode)

# 2. 5-min bars NR7 -> break of that 5-min bar's range in next bars (within 30 min)
df5 = pd.DataFrame({'day': day, 'b5': mod // 5, 'h': h, 'l': l})
g5 = df5.groupby(['day', 'b5']).agg(h=('h', 'max'), l=('l', 'min')).reset_index()
g5['r'] = g5['h'] - g5['l']
for K in (4, 7):
    g5['nr'] = g5.groupby('day')['r'].transform(lambda v: v.rolling(K, min_periods=K).min()) == g5['r']
    nr = g5[g5['nr']]
    key = {(d, b): (hh, ll) for d, b, hh, ll in zip(nr['day'], nr['b5'], nr['h'], nr['l'])}
    for mode in ('mom', 'fade'):
        sg = []
        for (d, b), (hh, ll) in key.items():
            # bars after the 5-min bar ends: mod in [5b+5, 5b+35)
            s = np.searchsorted(day, d)
            e = np.searchsorted(day, d, side='right')
            idx = np.arange(s, e)
            m = mod[idx]
            win = idx[(m >= 5 * b + 5) & (m < 5 * b + 35)]
            for i in win:
                if c[i] > hh: sg.append((i, 1 if mode == 'mom' else -1)); break
                if c[i] < ll: sg.append((i, -1 if mode == 'mom' else 1)); break
        add(sg, fam=f'nr{K}_5m', p=K, mode=mode)

# 3. volume-confirmed 30-bar Donchian break: breakout bar volume > 2x avg of last 30 bars
qavg = pd.Series(q).groupby(day).transform(lambda v: v.shift(1).rolling(30, min_periods=30).mean()).values
hh = roll_max_prev(h, day, 30); ll = roll_min_prev(l, day, 30)
for vk in (2.0, 3.0):
    up = (c > hh) & (q > vk * qavg); dn = (c < ll) & (q > vk * qavg)
    for mode in ('mom', 'fade'):
        sg = [(i, 1 if mode == 'mom' else -1) for i in np.flatnonzero(up)] + [(i, -1 if mode == 'mom' else 1) for i in np.flatnonzero(dn)]
        add(sg, fam='volbrk30', p=vk, mode=mode)

# 4. Bollinger squeeze: 20-bar std of close / 120-bar mean std in bottom 20%; then close outside 20-bar band (2 sd)
sd20 = pd.Series(c).rolling(20).std().values
ma20 = pd.Series(c).rolling(20).mean().values
sdl = pd.Series(sd20).shift(1).rolling(240, min_periods=120).mean().values
ratio = pd.Series(sd20 / sdl).shift(1).values
for thr in (0.6, 0.8):
    sqz = pd.Series(ratio < thr).rolling(10).max().values.astype(bool)  # squeeze present in last 10 bars
    up = sqz & (c > ma20 + 2 * sd20); dn = sqz & (c < ma20 - 2 * sd20)
    up, dn = edge_events(up, dn, day)
    for mode in ('mom', 'fade'):
        sg = [(i, 1 if mode == 'mom' else -1) for i in np.flatnonzero(up)] + [(i, -1 if mode == 'mom' else 1) for i in np.flatnonzero(dn)]
        add(sg, fam='bbsqz', p=thr, mode=mode)

R = pd.concat(res)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
print(R.groupby(['fam', 'p', 'mode']).agg(n=('n','mean'),tot_mean=('total','mean'),tot_min=('total','min'),tot_max=('total','max'),tmax=('t','max'),npos=('total',lambda x:(x>0).sum())))
print(R[R.apply(passes, axis=1)].to_string())
print('variants', VARIANTS[0])
