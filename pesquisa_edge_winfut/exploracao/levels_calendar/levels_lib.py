from harness import *

def first_touch_sigs(df, level, mode='touch', margin=0.0, tmin=0, tmax=480, once_per_day=True, require_open_side=True):
    """level: array per bar (may vary in time; NaN = none). approach dir a=+1 if from below.
    mode 'touch': bar high>=level (from below) / low<=level (from above), first time today.
    mode 'close': close beyond level by margin (first time), approach by side of day open.
    returns list (i, a) in FOLLOW orientation."""
    h = df['high'].values; l = df['low'].values; c = df['close'].values; o = df['open'].values
    day = df['day'].values; mod = df['mod'].values
    first = df['first_of_day'].values
    n = len(df); sigs = []
    side = 0; done_up = done_dn = False
    for i in range(n):
        if first[i]:
            done_up = done_dn = False
            L0 = level[i]
            side = 0 if np.isnan(L0) else (1 if o[i] < L0 else -1)   # 1: start below level
        L = level[i]
        if np.isnan(L): continue
        if mode == 'touch':
            up = h[i] >= L and (c[i-1] < L if not first[i] else o[i] < L)
            dn = l[i] <= L and (c[i-1] > L if not first[i] else o[i] > L)
        else:
            up = c[i] >= L + margin and (c[i-1] < L + margin if not first[i] else o[i] < L + margin)
            dn = c[i] <= L - margin and (c[i-1] > L - margin if not first[i] else o[i] > L - margin)
        if require_open_side:
            up = up and side == 1
            dn = dn and side == -1
        ok = tmin <= mod[i] <= tmax
        if up and not done_up:
            done_up = True if once_per_day else False
            if ok: sigs.append((i, 1))
        if dn and not done_dn:
            done_dn = True if once_per_day else False
            if ok: sigs.append((i, -1))
    return sigs
