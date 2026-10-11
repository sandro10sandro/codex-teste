from levels_lib import *
df = get(); f = features(df)
c = df['close'].values; h = df['high'].values; l = df['low'].values; o = df['open'].values
mod = df['mod'].values; day = df['day'].values; n = len(df); tm = df['time'].values
pdc = f.pdc.values; hod = f.hod.values; lod = f.lod.values; dopen = f.dopen.values
gf = (((dopen >= pdc) & (lod <= pdc)) | ((dopen <= pdc) & (hod >= pdc))) & ~np.isnan(pdc)
cnt = 0
for M in (45, 60, 75):
    orh = np.full(n, np.nan); orl = np.full(n, np.nan)
    for d, idx in df.groupby('day').indices.items():
        idx = np.sort(idx); m = mod[idx]
        sel = idx[m < M]; later = idx[m >= M]
        orh[later] = h[sel].max(); orl[later] = l[sel].min()
    H = first_touch_sigs(df, orh, 'close', 0, require_open_side=False)
    L = first_touch_sigs(df, orl, 'close', 0, require_open_side=False)
    out_ = [(i, d) for i, d in H if d == 1] + [(i, d) for i, d in L if d == -1]   # outward breaks
    in_ = [(i, d) for i, d in H if d == -1] + [(i, d) for i, d in L if d == 1]    # re-entries into range
    for nm, s in [('outward', out_), ('inward', in_), ('both', out_ + in_)]:
        for filt in ('gf', 'nogf', 'all'):
            if filt == 'gf': ss = [x for x in s if gf[x[0]]]
            elif filt == 'nogf': ss = [x for x in s if not gf[x[0]] and not np.isnan(pdc[x[0]])]
            else: ss = s
            out = []
            for T, S in [(300,400),(300,500),(400,500),(500,500),(400,400),(300,300)]:
                E, D, P = fastbt(df, [(i, -d) for i, d in ss], T, S); r = st(df, E, D, P); cnt += 1
                out.append(f"{T}/{S} n{r['n']} t{r['t']:+.1f}")
            print(f'M{M} {nm:8s} {filt:5s} FADE', ' | '.join(out))
add_count(cnt * 2)   # count follow orientation implicitly seen as negative mirror
print('variants so far', total_count())
