from levels_lib import *
df = get(); f = features(df)
c = df['close'].values; h = df['high'].values; l = df['low'].values
mod = df['mod'].values; first = df['first_of_day'].values; day = df['day'].values
n = len(df)
# opening range levels known after minute M
for M in (30, 60):
    orh = np.full(n, np.nan); orl = np.full(n, np.nan)
    g = df.groupby('day')
    for d, idx in g.indices.items():
        idx = np.sort(idx)
        m = mod[idx]
        sel = idx[m < M]
        H = h[sel].max(); L = l[sel].min()
        later = idx[m >= M]
        orh[later] = H; orl[later] = L
    # first break (close beyond) -> follow/fade
    s = first_touch_sigs(df, orh, 'close', 0, require_open_side=False) + first_touch_sigs(df, orl, 'close', 0, require_open_side=False)
    s = [x for x in s if mod[x[0]] >= M]
    evaluate(df, f'OR{M} first close-break', s)
    # retest after break: after a close above ORH, first later touch back of ORH from above -> follow = long (support)
    sr = []
    for d, idx in g.indices.items():
        idx = np.sort(idx); idx = idx[mod[idx] >= M]
        brk_up = brk_dn = False; done_u = done_d = False
        for i in idx:
            if brk_up and not done_u and l[i] <= orh[i] and c[i-1] > orh[i]:
                sr.append((i, 1)); done_u = True
            if brk_dn and not done_d and h[i] >= orl[i] and c[i-1] < orl[i]:
                sr.append((i, -1)); done_d = True
            if c[i] > orh[i] + 0.0: brk_up = True
            if c[i] < orl[i] - 0.0: brk_dn = True
    evaluate(df, f'OR{M} retest after break', sr)
# VWAP touch: cross of vwap after being away >= X pct; follow = continue across
pv = (df['close'] * df['qty']).groupby(df['day']).cumsum(); vq = df['qty'].groupby(df['day']).cumsum()
vwap = (pv / vq).values
for X in (0.2, 0.4):
    s = []
    away = 0
    for i in range(n):
        if first[i]: away = 0; continue
        if mod[i] < 15: continue
        dv = (c[i-1] - vwap[i-1]) / c[i] * 100
        if dv >= X: away = 1
        elif dv <= -X: away = -1
        if away == 1 and l[i] <= vwap[i]:
            s.append((i, -1)); away = 0
        elif away == -1 and h[i] >= vwap[i]:
            s.append((i, 1)); away = 0
    evaluate(df, f'VWAP return X{X}', s)
print('variants so far', total_count())
