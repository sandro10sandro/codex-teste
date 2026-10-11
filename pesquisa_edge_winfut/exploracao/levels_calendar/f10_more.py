from levels_lib import *
df = get(); f = features(df)
c = df['close'].values; h = df['high'].values; l = df['low'].values; o = df['open'].values
mod = df['mod'].values; first = df['first_of_day'].values; day = df['day'].values; n = len(df)
hod = f.hod.values; lod = f.lod.values
# --- ADR exhaustion
g = df.groupby('day').agg(h=('high', 'max'), l=('low', 'min'), c=('close', 'last'))
rngpct = (g.h - g.l) / g.c
for N in (5, 10):
    adr = rngpct.rolling(N, min_periods=N).mean().shift(1)   # prior N days avg range pct
    adr_b = df['day'].map(adr).values
    for k in (0.8, 1.0, 1.2):
        s = []; done = set()
        for i in range(n):
            if np.isnan(adr_b[i]) or day[i] in done: continue
            if (hod[i] - lod[i]) / c[i] >= k * adr_b[i]:
                # direction of the most recent extreme: if this bar made the new high -> +1 else -1
                d = 1 if h[i] >= hod[i] else (-1 if l[i] <= lod[i] else 0)
                if d != 0:
                    s.append((i, d)); done.add(day[i])
        evaluate(df, f'ADR{N} exhaustion k{k}', s)
# --- prior-day settlement proxy: VWAP of last M minutes of prior day; first touch follow/fade
for M in (15, 30):
    sub = df[df['mod'] >= 510 - M]
    sv = (sub['close'] * sub['qty']).groupby(sub['day']).sum() / sub['qty'].groupby(sub['day']).sum()
    lv = df['day'].map(sv.shift(1)).values
    evaluate(df, f'PD settle-proxy VWAP last{M} touch', first_touch_sigs(df, lv, 'touch', require_open_side=False))
# --- false break of PDH/PDL: high exceeds PDH, then within W bars a close back below PDH -> signal (follow orientation = direction of the false break, so fade = reversal)
pdh = f.pdh.values; pdl = f.pdl.values
for W in (5, 15, 30):
    s = []
    for dd, idx in df.groupby('day').indices.items():
        idx = np.sort(idx)
        if np.isnan(pdh[idx[0]]): continue
        tu = td = None; du = dn_ = False
        for i in idx:
            if tu is None and h[i] > pdh[i] and (i == idx[0] and o[i] < pdh[i] or i > idx[0] and c[i-1] <= pdh[i]): tu = i
            if td is None and l[i] < pdl[i] and (i == idx[0] and o[i] > pdl[i] or i > idx[0] and c[i-1] >= pdl[i]): td = i
            if tu is not None and not du and c[i] < pdh[i] and i - tu <= W:
                s.append((i, 1)); du = True
            if td is not None and not dn_ and c[i] > pdl[i] and i - td <= W:
                s.append((i, -1)); dn_ = True
    evaluate(df, f'PDH/PDL false-break W{W}', s)
print('variants so far', total_count())
