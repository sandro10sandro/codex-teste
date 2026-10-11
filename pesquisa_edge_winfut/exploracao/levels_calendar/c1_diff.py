from levels_lib import *
df = get(); f = features(df)
c = df['close'].values; h = df['high'].values; l = df['low'].values; o = df['open'].values
mod = df['mod'].values; day = df['day'].values; n = len(df); tm = df['time'].values
pdc = f.pdc.values; hod = f.hod.values; lod = f.lod.values; dopen = f.dopen.values
gf = (((dopen >= pdc) & (lod <= pdc)) | ((dopen <= pdc) & (hod >= pdc))) & ~np.isnan(pdc)
M = 60
orh = np.full(n, np.nan); orl = np.full(n, np.nan)
for d, idx in df.groupby('day').indices.items():
    idx = np.sort(idx); m = mod[idx]
    sel = idx[m < M]; later = idx[m >= M]
    orh[later] = h[sel].max(); orl[later] = l[sel].min()
A = first_touch_sigs(df, orh, 'close', 0, require_open_side=False) + first_touch_sigs(df, orl, 'close', 0, require_open_side=False)
A = sorted([x for x in A if mod[x[0]] >= M and gf[x[0]]])
print(len(A))
for i, d in A[:20]:
    print(df['date'].values[i], tm[i], d, 'c', round(c[i]), 'orh', round(orh[i]), 'orl', round(orl[i]), 'c[i-1]', round(c[i-1]))
