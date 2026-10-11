from levels_lib import *
df = get(); f = features(df)
c = df['close'].values; h = df['high'].values; l = df['low'].values
mod = df['mod'].values; n = len(df); day = df['day'].values
pdc = f.pdc.values; hod = f.hod.values; lod = f.lod.values; dopen = f.dopen.values
gf = (((dopen >= pdc) & (lod <= pdc)) | ((dopen <= pdc) & (hod >= pdc))) & ~np.isnan(pdc)
M = 60
orh = np.full(n, np.nan); orl = np.full(n, np.nan)
for d, idx in df.groupby('day').indices.items():
    idx = np.sort(idx); m = mod[idx]
    sel = idx[m < M]; later = idx[m >= M]
    orh[later] = h[sel].max(); orl[later] = l[sel].min()
ev = []
for dd, idx in df.groupby('day').indices.items():
    idx = np.sort(idx)
    if np.isnan(pdc[idx[0]]): continue
    du = dn = False
    for i in idx:
        if mod[i] < M: continue
        if c[i] >= orh[i] and not du and c[i-1] < orh[i]: du = True; ev.append((i, 1))
        if c[i] <= orl[i] and not dn and c[i-1] > orl[i]: dn = True; ev.append((i, -1))
s = [(i, -d if gf[i] else d) for i, d in ev]
E, D, P = fastbt(df, s, 300, 500); r0 = st(df, E, D, P); print('actual', r0)
# permutation: shuffle the gf label across events (keeps count of fade vs follow)
rng = np.random.default_rng(42)
lab = np.array([gf[i] for i, d in ev])
ts = []; tots = []
for k in range(2000):
    pl = rng.permutation(lab)
    s2 = [(i, -d if g else d) for (i, d), g in zip(ev, pl)]
    E, D, P = fastbt(df, s2, 300, 500); r = st(df, E, D, P); ts.append(r['t']); tots.append(r['total'])
ts = np.array(ts); tots = np.array(tots)
print('perm mean t', ts.mean().round(2), 'p(t>=actual)', (ts >= r0['t']).mean(), 'p(total>=actual)', (tots >= r0['total']).mean())
# all-follow and all-fade references
for nm, s3 in [('all follow', ev), ('all fade', [(i, -d) for i, d in ev])]:
    E, D, P = fastbt(df, s3, 300, 500); print(nm, st(df, E, D, P))
