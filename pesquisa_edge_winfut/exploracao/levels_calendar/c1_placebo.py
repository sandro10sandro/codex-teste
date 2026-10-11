from levels_lib import *
df = get(); f = features(df)
c = df['close'].values; h = df['high'].values; l = df['low'].values
mod = df['mod'].values; day = df['day'].values; n = len(df)
pdc = f.pdc.values; hod = f.hod.values; lod = f.lod.values; dopen = f.dopen.values
pdh = f.pdh.values; pdl = f.pdl.values; pdo = f.pdo.values
def crossed(X):
    return (((dopen >= X) & (lod <= X)) | ((dopen <= X) & (hod >= X))) & ~np.isnan(X)
def or_sigs(M):
    orh = np.full(n, np.nan); orl = np.full(n, np.nan)
    for d, idx in df.groupby('day').indices.items():
        idx = np.sort(idx); m = mod[idx]
        sel = idx[m < M]; later = idx[m >= M]
        orh[later] = h[sel].max(); orl[later] = l[sel].min()
    s = first_touch_sigs(df, orh, 'close', 0, require_open_side=False) + first_touch_sigs(df, orl, 'close', 0, require_open_side=False)
    return [x for x in s if mod[x[0]] >= M]
base = or_sigs(60)
TS4 = [(300,400),(300,500),(400,500),(500,500)]
levels = {'PDC': pdc, 'PDC+0.3%': pdc*1.003, 'PDC-0.3%': pdc*0.997, 'PDC+0.6%': pdc*1.006, 'PDC-0.6%': pdc*0.994,
          'PDmid': (pdh+pdl)/2, 'PDO': pdo, 'PDH': pdh, 'PDL': pdl}
for nm, X in levels.items():
    cr = crossed(X)
    s = [x for x in base if cr[x[0]]]
    su = [x for x in base if not cr[x[0]] and not np.isnan(X[x[0]])]
    out = []
    for T, S in TS4:
        E, D, P = fastbt(df, [(i, -d) for i, d in s], T, S); r = st(df, E, D, P)
        E2, D2, P2 = fastbt(df, [(i, -d) for i, d in su], T, S); r2 = st(df, E2, D2, P2)
        out.append(f"{T}/{S}: crossed n{r['n']} t{r['t']:+.1f} | not n{r2['n']} t{r2['t']:+.1f}")
    print(f'{nm:9s}', ' ; '.join(out))
add_count(len(levels) * 4 * 2)
print('variants so far', total_count())
