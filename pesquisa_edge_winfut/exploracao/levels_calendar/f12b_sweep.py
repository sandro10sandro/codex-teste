from levels_lib import *
df = get(); f = features(df)
c = df['close'].values; h = df['high'].values; l = df['low'].values
mod = df['mod'].values; day = df['day'].values; n = len(df)
pdc = f.pdc.values; hod = f.hod.values; lod = f.lod.values; dopen = f.dopen.values
gapfilled = (((dopen >= pdc) & (lod <= pdc)) | ((dopen <= pdc) & (hod >= pdc))) & ~np.isnan(pdc)
def or_sigs(M):
    orh = np.full(n, np.nan); orl = np.full(n, np.nan)
    for d, idx in df.groupby('day').indices.items():
        idx = np.sort(idx); m = mod[idx]
        sel = idx[m < M]; later = idx[m >= M]
        orh[later] = h[sel].max(); orl[later] = l[sel].min()
    s = first_touch_sigs(df, orh, 'close', 0, require_open_side=False) + first_touch_sigs(df, orl, 'close', 0, require_open_side=False)
    return [x for x in s if mod[x[0]] >= M]
for M in (50, 55, 65, 70, 75, 90, 105, 120, 150):
    s = or_sigs(M)
    sf = [x for x in s if gapfilled[x[0]]]
    evaluate(df, f'OR{M} break | gap filled', sf, orient=(-1,))
print('variants so far', total_count())
