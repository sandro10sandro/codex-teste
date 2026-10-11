"""Causal volume/flow features for research (volume_flow lens)."""
import numpy as np, pandas as pd

def tod_norm(df, col, ndays=10, minp=3):
    """col[i] / median of col at same minute-of-day over the previous ndays days (strictly prior days)."""
    piv = df.pivot_table(index='day', columns='mod', values=col, aggfunc='first')
    med = piv.shift(1).rolling(ndays, min_periods=minp).median()
    m = med.stack()
    key = pd.MultiIndex.from_arrays([df['day'].values, df['mod'].values])
    norm = m.reindex(key).values
    return df[col].values / norm

def add_features(df):
    df = df.copy()
    h, l, c, o = df.high.values, df.low.values, df.close.values, df.open.values
    rngb = h - l
    clv = np.where(rngb > 0, (2*c - h - l) / np.where(rngb > 0, rngb, 1), 0.0)
    df['clv'] = clv
    df['ats'] = df.qty / df.trades
    df['rv_tod'] = tod_norm(df, 'qty')
    df['rt_tod'] = tod_norm(df, 'trades')
    df['ats_tod'] = tod_norm(df.assign(ats=df.qty/df.trades), 'ats')
    df['rng_tod'] = tod_norm(df.assign(rngb=rngb), 'rngb')
    g = df.groupby('day')
    for N in (5, 10, 20, 60):
        df[f'rv_loc{N}'] = df.qty / g.qty.transform(lambda s: s.shift(1).rolling(N, min_periods=N).mean())
    df['ret1'] = c - g.close.shift(1).values
    for N in (3, 5, 10, 15, 30, 60):
        df[f'ret{N}'] = c - g.close.shift(N).values
        cq = (df.clv * df.qty)
        df[f'press{N}'] = cq.groupby(df.day).transform(lambda s: s.rolling(N, min_periods=N).sum()) / \
                          df.qty.groupby(df.day).transform(lambda s: s.rolling(N, min_periods=N).sum())
        sv = np.sign(df.close - df.open) * df.qty
        df[f'sv{N}'] = sv.groupby(df.day).transform(lambda s: s.rolling(N, min_periods=N).sum()) / \
                          df.qty.groupby(df.day).transform(lambda s: s.rolling(N, min_periods=N).sum())
    # day-level: cumulative signed volume since open (normalized)
    sv = np.sign(df.close - df.open) * df.qty
    df['csv_day'] = sv.groupby(df.day).cumsum() / df.qty.groupby(df.day).cumsum()
    cq = df.clv * df.qty
    df['cpress_day'] = cq.groupby(df.day).cumsum() / df.qty.groupby(df.day).cumsum()
    # vwap of the day (real-price based not needed; deviation relative)
    tp = (df.high + df.low + df.close) / 3
    df['vwap'] = (tp * df.qty).groupby(df.day).cumsum() / df.qty.groupby(df.day).cumsum()
    df['dvwap'] = df.close - df.vwap
    df['ret_day'] = df.close - g.open.transform('first')
    return df
