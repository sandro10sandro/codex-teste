from sym import *
h = df['high'].values; l = df['low'].values; c = df['close'].values; o = df['open'].values
mod = df['mod'].values
first = df['first_of_day'].values
s = pd.Series
hs_prev = s(h).groupby(day).transform(lambda x: x.cummax().shift(1)).values
ls_prev = s(l).groupby(day).transform(lambda x: x.cummin().shift(1)).values
tp = (h + l + c) / 3; q = df['qty'].values
vwap = s(tp*q).groupby(day).cumsum().values / s(q).groupby(day).cumsum().values
vwap_prev = s(vwap).groupby(day).shift(1).values
c_prev = s(c).groupby(day).shift(1).values

def ev_new_extreme(min_mod=30):
    """+1 when close breaks above previous session high (first time in last 15 bars), -1 below low."""
    up = (c > hs_prev) & (mod >= min_mod)
    dn = (c < ls_prev) & (mod >= min_mod)
    e = np.zeros(n, int); e[up] = 1; e[dn] = -1
    return e

def ev_vwap_cross(min_mod=30):
    up = (c > vwap) & (c_prev <= vwap_prev) & (mod >= min_mod)
    dn = (c < vwap) & (c_prev >= vwap_prev) & (mod >= min_mod)
    e = np.zeros(n, int); e[up] = 1; e[dn] = -1
    return e

def ev_big_bar(k=3.0, min_mod=5):
    r1 = F['r1'].values; v = np.maximum(F['vol60'].values, 1.0)
    e = np.zeros(n, int)
    e[(r1 > k * v) & (mod >= min_mod)] = 1; e[(r1 < -k * v) & (mod >= min_mod)] = -1
    return e

def ev_orb(rng_min=30):
    """opening range breakout: first close beyond the first rng_min-minute range."""
    in_or = mod < rng_min
    orh = s(np.where(in_or, h, -np.inf)).groupby(day).cummax().values
    orl = s(np.where(in_or, l, np.inf)).groupby(day).cummin().values
    up = (mod >= rng_min) & (c > orh); dn = (mod >= rng_min) & (c < orl)
    e = np.zeros(n, int); e[up] = 1; e[dn] = -1
    # only the first event of each side per day
    out = np.zeros(n, int)
    for sgn in (1, -1):
        m = e == sgn
        firsts = s(m).groupby(day).cumsum().values == 1
        out[m & firsts] = sgn
    return out

def base_rates(e, T, S):
    yl, ys = labels(T, S)
    idx = np.flatnonzero((e != 0) & valid)
    d = e[idx]
    y_with = np.where(d == 1, yl[idx], ys[idx]); y_fade = np.where(d == 1, ys[idx], yl[idx])
    h1 = day[idx] < 30
    return dict(n=len(idx), with_h1=round(np.nanmean(y_with[h1]),1), with_h2=round(np.nanmean(y_with[~h1]),1),
                fade_h1=round(np.nanmean(y_fade[h1]),1), fade_h2=round(np.nanmean(y_fade[~h1]),1))
