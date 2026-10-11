from levels_lib import *
df = get(); f = features(df)
c = df['close'].values; h = df['high'].values; l = df['low'].values
mod = df['mod'].values; day = df['day'].values; n = len(df)
pdc = f.pdc.values; hod = f.hod.values; lod = f.lod.values; dopen = f.dopen.values
gapfilled = (((dopen >= pdc) & (lod <= pdc)) | ((dopen <= pdc) & (hod >= pdc))) & ~np.isnan(pdc)
def or_sigs(M):
    orh = np.full(n, np.nan); orl = np.full(n, np.nan)
    for d, idx in df.groupby('day').indices.items():
        idx = np.sort(idx); m = mod[idx]
        sel = idx[m < M]; later = idx[m >= M]
        orh[later] = h[sel].max(); orl[later] = l[sel].min()
    s = first_touch_sigs(df, orh, 'close', 0, require_open_side=False) + first_touch_sigs(df, orl, 'close', 0, require_open_side=False)
    return [x for x in s if mod[x[0]] >= M]
s = [(i, -d) for i, d in or_sigs(60) if gapfilled[i]]
for T, S in [(300,400),(300,500),(400,400),(400,500),(500,500),(200,500),(300,300),(500,400)]:
    tr, stt = wf.backtest(df, s, T, S, 'base')
    trs, sts = wf.backtest(df, s, T, S, 'stress')
    rb = wf.random_baseline(df, tr, T, S, 'base', n_iter=2000)
    tr['month'] = tr['date'] // 100
    mon = tr.groupby('month')['pnl'].sum().round(0).to_dict()
    print(T, S, {k: stt[k] for k in ['n','total','avg','win_rate','t_daily','first_half_total','second_half_total','long_n','long_total','short_n','short_total','eod']}, 'stress', sts['total'], 'p', rb['p_value'], mon)
add_count(0)
