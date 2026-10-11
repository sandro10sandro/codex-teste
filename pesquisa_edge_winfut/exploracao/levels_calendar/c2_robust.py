from levels_lib import *
df = get(); f = features(df)
c = df['close'].values; h = df['high'].values; l = df['low'].values; o = df['open'].values
mod = df['mod'].values; day = df['day'].values; n = len(df); tm = df['time'].values; tick = df['tick'].values
pdc = f.pdc.values; hod = f.hod.values; lod = f.lod.values; dopen = f.dopen.values
gf_dyn = (((dopen >= pdc) & (lod <= pdc)) | ((dopen <= pdc) & (hod >= pdc))) & ~np.isnan(pdc)
M = 60
orh = np.full(n, np.nan); orl = np.full(n, np.nan); gf_static = np.zeros(n, bool)
for d, idx in df.groupby('day').indices.items():
    idx = np.sort(idx); m = mod[idx]
    sel = idx[m < M]; later = idx[m >= M]
    orh[later] = h[sel].max(); orl[later] = l[sel].min()
    gf_static[later] = gf_dyn[sel[-1]]
def build(strict=False, margin_ticks=0, gfarr=gf_dyn, tmax=480, first_only=False):
    s = []
    for dd, idx in df.groupby('day').indices.items():
        idx = np.sort(idx)
        if np.isnan(pdc[idx[0]]): continue
        du = dn = False
        for i in idx:
            if mod[i] < M: continue
            mg = margin_ticks * tick[i]
            up = (c[i] > orh[i] + mg) if strict else (c[i] >= orh[i] + mg)
            dw = (c[i] < orl[i] - mg) if strict else (c[i] <= orl[i] - mg)
            # require crossing from inside (prev close inside)
            if up and not du and c[i-1] < orh[i] + mg:
                du = True
                if mod[i] <= tmax and not (first_only and dn): s.append((i, -1 if gfarr[i] else 1))
            if dw and not dn and c[i-1] > orl[i] - mg:
                dn = True
                if mod[i] <= tmax and not (first_only and du and s and s[-1][0] != i): s.append((i, 1 if gfarr[i] else -1))
    return s
cnt = 0
variants = [('base', {}), ('strict', dict(strict=True)), ('margin1', dict(margin_ticks=1)), ('margin2', dict(margin_ticks=2)),
            ('gf_static10h', dict(gfarr=gf_static)), ('tmax 13h', dict(tmax=240)), ('tmax 15h', dict(tmax=360)), ('first_only', dict(first_only=True))]
for nm, kw in variants:
    s = build(**kw)
    out = []
    for T, S in [(300,400),(300,500),(400,500),(500,500),(400,400),(200,500)]:
        E, D, P = fastbt(df, s, T, S); r = st(df, E, D, P); cnt += 1
        out.append(f"{T}/{S} n{r['n']} t{r['t']:+.1f} h{r['h1']:+.0f}/{r['h2']:+.0f}")
    print(f'{nm:13s}', ' | '.join(out))
add_count(cnt)
print('variants so far', total_count())
