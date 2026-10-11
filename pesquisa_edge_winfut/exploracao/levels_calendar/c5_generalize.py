from levels_lib import *
df = get(); f = features(df)
c = df['close'].values; h = df['high'].values; l = df['low'].values
mod = df['mod'].values; n = len(df); first = df['first_of_day'].values
pdc = f.pdc.values; hod = f.hod.values; lod = f.lod.values; dopen = f.dopen.values
pdh = f.pdh.values; pdl = f.pdl.values
gf = (((dopen >= pdc) & (lod <= pdc)) | ((dopen <= pdc) & (hod >= pdc))) & ~np.isnan(pdc)
def cond(ev):
    return [(i, -d if gf[i] else d) for i, d in ev if not np.isnan(pdc[i])]
fam = {}
# PDH/PDL outward close breaks
H = first_touch_sigs(df, pdh, 'close', 0, require_open_side=False); L = first_touch_sigs(df, pdl, 'close', 0, require_open_side=False)
fam['PDH/PDL outward'] = [(i, d) for i, d in H if d == 1] + [(i, d) for i, d in L if d == -1]
# HOD/LOD close-break after L minutes
for LL in (30, 60):
    s = []
    for i in range(n):
        if first[i]: Hh = h[i]; Lo = l[i]; tH = tL = i; continue
        if c[i] > Hh and i - tH >= LL and mod[i] >= 30: s.append((i, 1))
        if c[i] < Lo and i - tL >= LL and mod[i] >= 30: s.append((i, -1))
        if h[i] > Hh: Hh = h[i]; tH = i
        if l[i] < Lo: Lo = l[i]; tL = i
    fam[f'HODLOD close L{LL}'] = s
# OR30 outward
for M in (30, 120):
    orh = np.full(n, np.nan); orl = np.full(n, np.nan)
    for d, idx in df.groupby('day').indices.items():
        idx = np.sort(idx); m = mod[idx]; sel = idx[m < M]; later = idx[m >= M]
        orh[later] = h[sel].max(); orl[later] = l[sel].min()
    H = first_touch_sigs(df, orh, 'close', 0, require_open_side=False); L = first_touch_sigs(df, orl, 'close', 0, require_open_side=False)
    fam[f'OR{M} outward'] = [(i, d) for i, d in H if d == 1] + [(i, d) for i, d in L if d == -1]
cnt = 0
for nm, ev in fam.items():
    s = cond(ev)
    line = []
    for T, S in TS:
        E, D, P = fastbt(df, s, T, S); r = st(df, E, D, P); cnt += 1
        line.append(f"{r['t']:+.1f}")
    # arms separately at 300/500
    fa = [(i, -d) for i, d in ev if gf[i]]; fo = [(i, d) for i, d in ev if not gf[i] and not np.isnan(pdc[i])]
    ra = st(df, *fastbt(df, fa, 300, 500)); ro = st(df, *fastbt(df, fo, 300, 500)); cnt += 2
    print(f'{nm:18s} n~{r["n"]} t[16]:', ' '.join(line), f"| arms@300/500 fade(gf) n{ra['n']} t{ra['t']:+.1f}  follow(!gf) n{ro['n']} t{ro['t']:+.1f}")
add_count(cnt)
print('variants so far', total_count())
