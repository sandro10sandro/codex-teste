from levels_lib import *
df = get(); f = features(df)
c = df['close'].values; h = df['high'].values; l = df['low'].values; o = df['open'].values
mod = df['mod'].values; day = df['day'].values; n = len(df); tm = df['time'].values
pdc = f.pdc.values; hod = f.hod.values; lod = f.lod.values; dopen = f.dopen.values
gf = (((dopen >= pdc) & (lod <= pdc)) | ((dopen <= pdc) & (hod >= pdc))) & ~np.isnan(pdc)
M = 60
orh = np.full(n, np.nan); orl = np.full(n, np.nan)
for d, idx in df.groupby('day').indices.items():
    idx = np.sort(idx); m = mod[idx]
    sel = idx[m < M]; later = idx[m >= M]
    orh[later] = h[sel].max(); orl[later] = l[sel].min()
H = first_touch_sigs(df, orh, 'close', 0, require_open_side=False)
L = first_touch_sigs(df, orl, 'close', 0, require_open_side=False)
out_ = [(i, d) for i, d in H if d == 1] + [(i, d) for i, d in L if d == -1]
s = [(i, -d if gf[i] else d) for i, d in out_ if not np.isnan(pdc[i])]
arm = {i: ('fade' if gf[i] else 'follow') for i, d in out_}
for T, S in [(300,500),(300,400),(400,500),(500,500),(200,500),(400,400)]:
    tr, stt = wf.backtest(df, s, T, S, 'base')
    trs, sts = wf.backtest(df, s, T, S, 'stress')
    rb = wf.random_baseline(df, tr, T, S, 'base', n_iter=2000)
    tr['month'] = tr['date'] // 100; tr['arm'] = tr['signal'].map(arm)
    mon = tr.groupby('month')['pnl'].sum().round(0).to_dict()
    arms = tr.groupby('arm')['pnl'].agg(['count', 'sum']).round(0).to_dict('index')
    print(T, S, {k: stt[k] for k in ['n','total','avg','win_rate','t_daily','first_half_total','second_half_total','long_n','long_total','short_n','short_total','eod','max_dd']}, 'stress', sts['total'], 'p', rb['p_value'], mon, arms)
