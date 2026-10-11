from harness import *
df = get(); f = features(df)
mod = df['mod'].values; day = df['day'].values
# gap follow signals: dir = sign(open - pdc); at bar k of day, only if gap not yet filled by close of bar k
gap = (f['dopen'] - f['pdc']).values
hod = f['hod'].values; lod = f['lod'].values; pdc = f['pdc'].values
for k in (0, 4, 14, 29, 59):
    for gmin in (0, 400, 800):
        sigs = []
        for i in np.flatnonzero(mod == k):
            g = gap[i]
            if np.isnan(g) or abs(g) < gmin or g == 0: continue
            filled = (lod[i] <= pdc[i]) if g > 0 else (hod[i] >= pdc[i])
            if filled: continue
            sigs.append((i, int(np.sign(g))))
        evaluate(df, f'gap k={k} g>={gmin}', sigs)
print('variants so far', total_count())
