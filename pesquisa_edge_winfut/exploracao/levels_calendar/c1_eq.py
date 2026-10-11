from levels_lib import *
df = get(); f = features(df)
c = df['close'].values; h = df['high'].values; l = df['low'].values; tick = df['tick'].values
mod = df['mod'].values; day = df['day'].values; n = len(df)
pdc = f.pdc.values; hod = f.hod.values; lod = f.lod.values; dopen = f.dopen.values
gf = (((dopen >= pdc) & (lod <= pdc)) | ((dopen <= pdc) & (hod >= pdc))) & ~np.isnan(pdc)
def orlv(M):
    orh = np.full(n, np.nan); orl = np.full(n, np.nan)
    for d, idx in df.groupby('day').indices.items():
        idx = np.sort(idx); m = mod[idx]
        sel = idx[m < M]; later = idx[m >= M]
        orh[later] = h[sel].max(); orl[later] = l[sel].min()
    return orh, orl
cnt = 0
for M in (45, 60, 75):
    orh, orl = orlv(M)
    eps = 1e-6
    for nm in ('ge', 'gt', 'eq'):
        s = []
        for dd, idx in df.groupby('day').indices.items():
            idx = np.sort(idx); du = dn = False
            for i in idx:
                if mod[i] < M: continue
                if nm == 'ge': up = c[i] >= orh[i] - eps; dw = c[i] <= orl[i] + eps
                elif nm == 'gt': up = c[i] > orh[i] + eps; dw = c[i] < orl[i] - eps
                else: up = abs(c[i] - orh[i]) < eps; dw = abs(c[i] - orl[i]) < eps
                if up and not du:
                    du = True
                    if gf[i]: s.append((i, -1))
                if dw and not dn:
                    dn = True
                    if gf[i]: s.append((i, 1))
        out = []
        for T, S in [(300,400),(300,500),(400,500),(500,500),(400,400),(200,500)]:
            E, D, P = fastbt(df, s, T, S); r = st(df, E, D, P); cnt += 1
            out.append(f"{T}/{S} n{r['n']} t{r['t']:+.1f}")
        print(M, nm, ' | '.join(out))
add_count(cnt)
print('variants so far', total_count())
