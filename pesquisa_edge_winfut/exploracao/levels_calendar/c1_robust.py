from levels_lib import *
df = get(); f = features(df)
c = df['close'].values; h = df['high'].values; l = df['low'].values; tick = df['tick'].values
mod = df['mod'].values; day = df['day'].values; n = len(df); tm = df['time'].values
pdc = f.pdc.values; hod = f.hod.values; lod = f.lod.values; dopen = f.dopen.values
gf = (((dopen >= pdc) & (lod <= pdc)) | ((dopen <= pdc) & (hod >= pdc))) & ~np.isnan(pdc)
def orlv(M):
    orh = np.full(n, np.nan); orl = np.full(n, np.nan)
    for d, idx in df.groupby('day').indices.items():
        idx = np.sort(idx); m = mod[idx]
        sel = idx[m < M]; later = idx[m >= M]
        orh[later] = h[sel].max(); orl[later] = l[sel].min()
    return orh, orl
orh, orl = orlv(60)
cnt = 0
# margin variants (in ticks) and touch mode
for mode, mt in [('close', 0), ('close', 1), ('close', 2), ('close', 4), ('touch', 0)]:
    s = []
    for dd, idx in df.groupby('day').indices.items():
        idx = np.sort(idx); du = dn = False
        for i in idx:
            if mod[i] < 60: continue
            m = mt * tick[i]
            if mode == 'close':
                up = c[i] > orh[i] + m; dn_ = c[i] < orl[i] - m
            else:
                up = h[i] > orh[i]; dn_ = l[i] < orl[i]
            if up and not du:
                du = True
                if gf[i]: s.append((i, -1))
            if dn_ and not dn:
                dn = True
                if gf[i]: s.append((i, 1))
    out = []
    for T, S in [(300,400),(300,500),(400,500),(500,500),(400,400)]:
        E, D, P = fastbt(df, s, T, S); r = st(df, E, D, P); cnt += 1
        out.append(f"{T}/{S} n{r['n']} t{r['t']:+.1f} tot{r['total']:+.0f}")
    print(mode, mt, ' | '.join(out))
add_count(cnt)
# daily pnl distribution and bootstrap for base rule 300/400
s = []
for dd, idx in df.groupby('day').indices.items():
    idx = np.sort(idx); du = dn = False
    for i in idx:
        if mod[i] < 60: continue
        if c[i] > orh[i] and not du:
            du = True
            if gf[i]: s.append((i, -1))
        if c[i] < orl[i] and not dn:
            dn = True
            if gf[i]: s.append((i, 1))
tr, stt = wf.backtest(df, s, 300, 400, 'base')
print('signal times', np.percentile(tr['time'], [0, 25, 50, 75, 100]))
daily = tr.groupby('date')['pnl'].sum().sort_values()
print('days traded', len(daily), 'worst5', daily.head(5).round(0).tolist(), 'best5', daily.tail(5).round(0).tolist())
allp = tr['pnl'].values
# drop the best 3 days
print('total minus best 3 days', round(daily.iloc[:-3].sum(), 0))
rng = np.random.default_rng(0)
days = sorted(df['date'].unique())
dser = tr.groupby('date')['pnl'].sum().reindex(days, fill_value=0).values
boots = [rng.choice(dser, len(dser)).sum() for _ in range(5000)]
print('bootstrap P(total<=0)', np.mean(np.array(boots) <= 0))
print('exit kinds', tr['kind'].value_counts().to_dict())
# hold time
print('hold minutes median', np.median(tr['exit'] - tr['entry']))
