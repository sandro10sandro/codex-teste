from levels_lib import *
df = get(); f = features(df)
c = df['close'].values; h = df['high'].values; l = df['low'].values; o = df['open'].values
mod = df['mod'].values; day = df['day'].values; n = len(df); tm = df['time'].values
pdc = f.pdc.values; hod = f.hod.values; lod = f.lod.values; dopen = f.dopen.values
gf = (((dopen >= pdc) & (lod <= pdc)) | ((dopen <= pdc) & (hod >= pdc))) & ~np.isnan(pdc)
cnt = 0
res = {}
for M in (30, 45, 60, 75, 90):
    orh = np.full(n, np.nan); orl = np.full(n, np.nan)
    for d, idx in df.groupby('day').indices.items():
        idx = np.sort(idx); m = mod[idx]
        sel = idx[m < M]; later = idx[m >= M]
        orh[later] = h[sel].max(); orl[later] = l[sel].min()
    H = first_touch_sigs(df, orh, 'close', 0, require_open_side=False)
    L = first_touch_sigs(df, orl, 'close', 0, require_open_side=False)
    out_ = [(i, d) for i, d in H if d == 1] + [(i, d) for i, d in L if d == -1]
    s = [(i, -d if gf[i] else d) for i, d in out_ if not np.isnan(pdc[i])]
    line = []
    for T, S in TS:
        E, D, P = fastbt(df, s, T, S); r = st(df, E, D, P); cnt += 1
        res[(M, T, S)] = r
        line.append(f"{r['t']:+.1f}")
    print(f'M{M} n~{r["n"]} t[16]:', ' '.join(line))
add_count(cnt)
for M in (60, 75):
    for T, S in [(300,500),(400,500),(500,500),(500,400)]:
        print(M, T, S, res[(M, T, S)])
print('variants so far', total_count())
