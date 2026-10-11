from levels_lib import *
df = get(); f = features(df)
mod = df['mod'].values
gap = (f['dopen'] - f['pdc']).values
hod = f['hod'].values; lod = f['lod'].values; pdc = f['pdc'].values
cnt = 0
for T, S in [(500,500),(400,500),(300,300),(400,400)]:
    line = []
    for k in range(5, 61, 1):
        s = []
        for i in np.flatnonzero(mod == k):
            G = gap[i]
            if np.isnan(G) or G == 0: continue
            filled = (lod[i] <= pdc[i]) if G > 0 else (hod[i] >= pdc[i])
            if not filled: s.append((i, int(np.sign(G))))
        E, D, P = fastbt(df, s, T, S); r = st(df, E, D, P); cnt += 1
        line.append(f"{k}:{r['t']:+.1f}")
    print(T, S, ' '.join(line))
add_count(cnt)
print('variants so far', total_count())
