from levels_lib import *
df = get(); f = features(df)
c = df['close'].values; h = df['high'].values; l = df['low'].values
mod = df['mod'].values; n = len(df); first = df['first_of_day'].values
pdc = f.pdc.values; hod = f.hod.values; lod = f.lod.values; dopen = f.dopen.values
gf = (((dopen >= pdc) & (lod <= pdc)) | ((dopen <= pdc) & (hod >= pdc))) & ~np.isnan(pdc)
cnt = 0
def ev(LL, tmin):
    s = []
    for i in range(n):
        if first[i]: Hh = h[i]; Lo = l[i]; tH = tL = i; continue
        if c[i] > Hh and i - tH >= LL and mod[i] >= tmin: s.append((i, 1))
        if c[i] < Lo and i - tL >= LL and mod[i] >= tmin: s.append((i, -1))
        if h[i] > Hh: Hh = h[i]; tH = i
        if l[i] < Lo: Lo = l[i]; tL = i
    return s
for tmin in (0, 60):
    for LL in (20, 30, 45, 60):
        e = ev(LL, tmin)
        s = [(i, -d if gf[i] else d) for i, d in e if not np.isnan(pdc[i])]
        line = []
        for T, S in TS:
            E, D, P = fastbt(df, s, T, S); r = st(df, E, D, P); cnt += 1
            line.append(f"{r['t']:+.1f}")
        print(f'tmin{tmin} L{LL} n~{r["n"]}', ' '.join(line))
add_count(cnt)
# overlap with OR60 candidate trades
M = 60
orh = np.full(n, np.nan); orl = np.full(n, np.nan)
for d, idx in df.groupby('day').indices.items():
    idx = np.sort(idx); m = mod[idx]; sel = idx[m < M]; later = idx[m >= M]
    orh[later] = h[sel].max(); orl[later] = l[sel].min()
A = []
for dd, idx in df.groupby('day').indices.items():
    idx = np.sort(idx)
    if np.isnan(pdc[idx[0]]): continue
    du = dn = False
    for i in idx:
        if mod[i] < M: continue
        if c[i] >= orh[i] and not du and c[i-1] < orh[i]: du = True; A.append((i, -1 if gf[i] else 1))
        if c[i] <= orl[i] and not dn and c[i-1] > orl[i]: dn = True; A.append((i, 1 if gf[i] else -1))
B = [(i, -d if gf[i] else d) for i, d in ev(30, 0) if not np.isnan(pdc[i])]
tA, _ = wf.backtest(df, A, 300, 500); tB, _ = wf.backtest(df, B, 400, 500)
sa = set(zip(tA.entry, tA.dir)); sb = set(zip(tB.entry, tB.dir))
near = sum(1 for e, d in sb if any(abs(e - e2) <= 3 and d == d2 for e2, d2 in sa))
print('A trades', len(sa), 'B trades', len(sb), 'B within 3 bars of an A trade same dir', near)
dA = tA.groupby('date').pnl.sum(); dB = tB.groupby('date').pnl.sum()
days = sorted(df.date.unique()); print('daily pnl corr', np.corrcoef(dA.reindex(days, fill_value=0), dB.reindex(days, fill_value=0))[0, 1].round(2))
print('variants so far', total_count())
