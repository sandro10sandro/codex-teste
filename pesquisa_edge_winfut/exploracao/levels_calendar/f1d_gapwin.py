from levels_lib import *
df = get(); f = features(df)
mod = df['mod'].values
gap = (f['dopen'] - f['pdc']).values
hod = f['hod'].values; lod = f['lod'].values; pdc = f['pdc'].values
def sigs(k0, k1):
    s = []
    for i in np.flatnonzero((mod >= k0) & (mod <= k1)):
        G = gap[i]
        if np.isnan(G) or G == 0: continue
        filled = (lod[i] <= pdc[i]) if G > 0 else (hod[i] >= pdc[i])
        if not filled: s.append((i, int(np.sign(G))))
    return s
for k0, k1 in [(14, 59), (14, 89), (29, 89), (14, 179), (59, 179), (0, 479), (14, 479), (89, 479)]:
    evaluate(df, f'gap-unfilled cont win {k0}-{k1}', sigs(k0, k1), orient=(1,))
print('variants so far', total_count())
