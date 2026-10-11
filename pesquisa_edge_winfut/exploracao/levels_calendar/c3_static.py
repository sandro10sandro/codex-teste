from levels_lib import *
df = get(); f = features(df)
c = df['close'].values; h = df['high'].values; l = df['low'].values
mod = df['mod'].values; n = len(df)
pdc = f.pdc.values; hod = f.hod.values; lod = f.lod.values; dopen = f.dopen.values
gf_dyn = (((dopen >= pdc) & (lod <= pdc)) | ((dopen <= pdc) & (hod >= pdc))) & ~np.isnan(pdc)
cnt = 0
for M in (45, 50, 55, 60, 65, 70, 75, 90):
    orh = np.full(n, np.nan); orl = np.full(n, np.nan); gfs = np.zeros(n, bool)
    for d, idx in df.groupby('day').indices.items():
        idx = np.sort(idx); m = mod[idx]
        sel = idx[m < M]; later = idx[m >= M]
        orh[later] = h[sel].max(); orl[later] = l[sel].min(); gfs[later] = gf_dyn[sel[-1]]
    s = []
    for dd, idx in df.groupby('day').indices.items():
        idx = np.sort(idx)
        if np.isnan(pdc[idx[0]]): continue
        du = dn = False
        for i in idx:
            if mod[i] < M: continue
            if c[i] >= orh[i] and not du and c[i-1] < orh[i]:
                du = True; s.append((i, -1 if gfs[i] else 1))
            if c[i] <= orl[i] and not dn and c[i-1] > orl[i]:
                dn = True; s.append((i, 1 if gfs[i] else -1))
    line = []
    for T, S in TS:
        E, D, P = fastbt(df, s, T, S); r = st(df, E, D, P); cnt += 1
        line.append(f"{r['t']:+.1f}")
    print(f'static M{M} n~{r["n"]} t[16]:', ' '.join(line))
add_count(cnt)
print('variants so far', total_count())
