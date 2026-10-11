from levels_lib import *
df = get(); f = features(df)
mod = df['mod'].values
gap = (f['dopen'] - f['pdc']).values / df['close'].values * 100   # pct
hod = f['hod'].values; lod = f['lod'].values; pdc = f['pdc'].values
def sigs_for(k, g):
    s = []
    for i in np.flatnonzero(mod == k):
        G = gap[i]
        if np.isnan(G) or abs(G) < g or G == 0: continue
        filled = (lod[i] <= pdc[i]) if G > 0 else (hod[i] >= pdc[i])
        if not filled: s.append((i, int(np.sign(G))))
    return s
ks = (9, 14, 19, 29, 44, 59); gs = (0.0, 0.1, 0.2, 0.3, 0.5)
tab = {}
cnt = 0
for k in ks:
    for g in gs:
        s = sigs_for(k, g)
        for T, S in TS:
            E, D, P = fastbt(df, s, T, S); r = st(df, E, D, P); tab[(k, g, T, S)] = r; cnt += 1
add_count(cnt)
for T, S in [(300,300),(400,400),(500,500),(300,500),(500,300),(400,300),(200,400),(300,400),(400,500)]:
    print(f'--- {T}/{S}  rows k, cols gap% {gs}  (n,t,h1/h2)')
    for k in ks:
        print(f'k={k:3d} ' + ' | '.join(f"{tab[(k,g,T,S)]['n']:2d} {tab[(k,g,T,S)]['t']:+.1f} {tab[(k,g,T,S)]['h1']:+5.0f}/{tab[(k,g,T,S)]['h2']:+5.0f}" for g in gs))
print('variants so far', total_count())
