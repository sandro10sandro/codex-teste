from levels_lib import *
df = get(); f = features(df)
c = df['close'].values; day = df['day'].values
O_ = O()
# vwap
pv = (df['close'] * df['qty']).groupby(df['day']).cumsum(); vq = df['qty'].groupby(df['day']).cumsum()
vwap = (pv / vq).values
# minutes since HOD/LOD
first = df['first_of_day'].values; h = df['high'].values; l = df['low'].values
sinceH = np.zeros(len(df)); sinceL = np.zeros(len(df))
for i in range(len(df)):
    if first[i]: H = h[i]; Lo = l[i]; tH = tL = i
    if h[i] >= H: H = h[i]; tH = i
    if l[i] <= Lo: Lo = l[i]; tL = i
    sinceH[i] = i - tH; sinceL[i] = i - tL
rc = df['real_close'].values
F = pd.DataFrame({
  'pos_pdr': (c - f.pdl) / (f.pdh - f.pdl),
  'd_pdc': (c - f.pdc) / c * 100,
  'd_open': (c - f.dopen) / c * 100,
  'pos_dr': (c - f.lod) / (f.hod - f.lod),
  'dr_width': (f.hod - f.lod) / c * 100,
  'd_vwap': (c - vwap) / c * 100,
  'grid1000': (rc % 1000) / 1000,
  'grid500': (rc % 500) / 500,
  'sinceH_minus_sinceL': sinceH - sinceL,
  'gap_pct': (f.dopen - f.pdc) / c * 100,
})
ok = (df['time'].values < 170000) & (df['mod'].values >= 5)
e = np.arange(len(df)) + 1; e[-1] = len(df) - 1
for T, S in [(500, 500), (300, 300)]:
    lab = O_[('zero', T, S)][1][0][e]   # long pnl entering next bar, zero cost
    print(f'=== label long zero-cost {T}/{S}; mean {np.nanmean(lab[ok]):.1f}')
    for col in F.columns:
        x = F[col].values
        m = ok & ~np.isnan(x) & ~np.isnan(lab)
        qs = np.nanquantile(x[m], [0, .2, .4, .6, .8, 1])
        b = np.clip(np.searchsorted(qs, x, side='right') - 1, 0, 4)
        out = []
        for k in range(5):
            mk = m & (b == k)
            # day-clustered t
            dm = pd.Series(lab[mk]).groupby(day[mk]).mean()
            t = dm.mean() / (dm.std(ddof=1) / np.sqrt(len(dm)))
            out.append(f'{lab[mk].mean():+6.0f}({t:+.1f})')
        print(f'{col:22s} ' + ' '.join(out) + '   q=' + ' '.join(f'{q:.2f}' for q in qs[1:-1]))
add_count(10 * 2 * 10)
print('variants so far', total_count())
