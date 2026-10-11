from levels_lib import *
df = get(); f = features(df)
c = df['close'].values; h = df['high'].values; l = df['low'].values
mod = df['mod'].values; n = len(df); first = df['first_of_day'].values
pdc = f.pdc.values; hod = f.hod.values; lod = f.lod.values; dopen = f.dopen.values
gf = (((dopen >= pdc) & (lod <= pdc)) | ((dopen <= pdc) & (hod >= pdc))) & ~np.isnan(pdc)
cnt = 0
for LL in (20, 30, 45, 60, 90):
    s = []
    for i in range(n):
        if first[i]: Hh = h[i]; Lo = l[i]; tH = tL = i; continue
        if c[i] > Hh and i - tH >= LL and mod[i] >= 30: s.append((i, 1))
        if c[i] < Lo and i - tL >= LL and mod[i] >= 30: s.append((i, -1))
        if h[i] > Hh: Hh = h[i]; tH = i
        if l[i] < Lo: Lo = l[i]; tL = i
    s = [(i, -d if gf[i] else d) for i, d in s if not np.isnan(pdc[i])]
    line = []
    for T, S in TS:
        E, D, P = fastbt(df, s, T, S); r = st(df, E, D, P); cnt += 1
        line.append(f"{r['t']:+.1f}")
    print(f'HODLOD cond L{LL} n~{r["n"]}', ' '.join(line))
    if LL == 30:
        for T, S in [(300,500),(400,500),(500,500)]:
            tr, stt = wf.backtest(df, s, T, S); rb = wf.random_baseline(df, tr, T, S); trs, sts = wf.backtest(df, s, T, S, 'stress')
            print('   ', T, S, {k: stt[k] for k in ['n','total','t_daily','first_half_total','second_half_total']}, 'stress', sts['total'], 'p', rb['p_value'])
add_count(cnt)
print('variants so far', total_count())
