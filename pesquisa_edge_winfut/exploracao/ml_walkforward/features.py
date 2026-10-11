"""Causal features for WIN 1-min bars. Every feature at row i uses only rows <= i.
Price features are expressed in relative terms (fraction of price) or in ticks, never absolute levels."""
import numpy as np
import pandas as pd


def _grp_cum(x, day, func):
    return pd.Series(x).groupby(day).transform(func).values


def feats(df: pd.DataFrame) -> pd.DataFrame:
    o = df["open"].values.astype(float)
    h = df["high"].values.astype(float)
    l = df["low"].values.astype(float)
    c = df["close"].values.astype(float)
    q = df["qty"].values.astype(float)
    ntr = df["trades"].values.astype(float)
    day = df["day"].values
    mod = df["mod"].values.astype(float)
    n = len(df)
    s = pd.Series
    lc = np.log(c)
    F = {}
    first = df["first_of_day"].values
    # bar index inside day
    k = s(np.ones(n)).groupby(day).cumsum().values - 1
    F["mod"] = mod
    F["mod2"] = (mod - 255.0) ** 2 / 255.0 ** 2
    F["open_bucket"] = (mod < 30).astype(float)
    F["close_bucket"] = (mod >= 450).astype(float)

    # returns (in bp) over lookbacks, intra-day only (clipped at day start)
    dopen = s(o).groupby(day).transform("first").values
    for L in (1, 3, 5, 10, 15, 30, 60, 120):
        prev = s(lc).groupby(day).shift(L).values
        r = (lc - prev) * 1e4
        # if not enough bars in day, use return since day open
        r0 = (lc - np.log(dopen)) * 1e4
        r = np.where(np.isnan(r), r0, r)
        F[f"r{L}"] = r
    F["r_day"] = (lc - np.log(dopen)) * 1e4

    # previous-day features
    dd = df.groupby("day").agg(dh=("high", "max"), dl=("low", "min"), dc=("close", "last"), do=("open", "first"))
    prev = dd.shift(1)
    pc = prev["dc"].reindex(day).values
    ph = prev["dh"].reindex(day).values
    pl = prev["dl"].reindex(day).values
    po = prev["do"].reindex(day).values
    F["gap"] = np.nan_to_num((np.log(dopen) - np.log(pc)) * 1e4)
    F["d_prevclose"] = np.nan_to_num((lc - np.log(pc)) * 1e4)
    F["d_prevhigh"] = np.nan_to_num((lc - np.log(ph)) * 1e4)
    F["d_prevlow"] = np.nan_to_num((lc - np.log(pl)) * 1e4)
    F["prev_day_ret"] = np.nan_to_num((np.log(pc) - np.log(po)) * 1e4)
    F["prev_range"] = np.nan_to_num((np.log(ph) - np.log(pl)) * 1e4)

    # session high / low so far
    hs = s(h).groupby(day).cummax().values
    ls = s(l).groupby(day).cummin().values
    rng = np.maximum(hs - ls, 1e-9)
    F["pos_in_range"] = (c - ls) / rng
    F["range_so_far"] = (np.log(hs) - np.log(ls)) * 1e4
    F["d_high"] = (lc - np.log(hs)) * 1e4
    F["d_low"] = (lc - np.log(ls)) * 1e4

    # VWAP so far (typical price)
    tp = (h + l + c) / 3.0
    cpv = s(tp * q).groupby(day).cumsum().values
    cv = s(q).groupby(day).cumsum().values
    vwap = cpv / np.maximum(cv, 1e-9)
    F["d_vwap"] = (lc - np.log(vwap)) * 1e4

    # volatility: rolling mean abs 1-min return and bar range (cross-day rolling ok, causal)
    r1 = np.r_[0.0, np.diff(lc)] * 1e4
    r1[first] = 0.0
    br = (np.log(h) - np.log(l)) * 1e4
    for L in (15, 60):
        F[f"vol{L}"] = s(np.abs(r1)).rolling(L, min_periods=1).mean().values
        F[f"brng{L}"] = s(br).rolling(L, min_periods=1).mean().values
    F["vol_ratio"] = np.maximum(F["vol15"], 0.5) / np.maximum(F["vol60"], 0.5)
    # normalized returns
    for L in (5, 15, 30, 60):
        F[f"z{L}"] = F[f"r{L}"] / (np.maximum(F["vol60"], 1.0) * np.sqrt(L))
    F["z_vwap"] = F["d_vwap"] / (np.maximum(F["vol60"], 1.0) * np.sqrt(60))
    F["z_day"] = F["r_day"] / (np.maximum(F["vol60"], 1.0) * np.sqrt(np.maximum(k, 1)))

    # volume features
    for L in (5, 15, 60):
        F[f"q{L}"] = s(q).rolling(L, min_periods=1).mean().values
    F["q_ratio5_60"] = F["q5"] / np.maximum(F["q60"], 1e-9)
    F["q_ratio15_60"] = F["q15"] / np.maximum(F["q60"], 1e-9)
    # volume vs the same minute on prior days (expanding mean of past days at same mod)
    qdf = pd.DataFrame({"mod": mod, "day": day, "q": q})
    past_same = qdf.groupby("mod")["q"].transform(lambda x: x.shift(1).expanding().mean()).values
    exp_q = s(q).expanding().mean().values
    past_same = np.where(np.isnan(past_same), exp_q, past_same)
    F["q_vs_tod"] = np.log((q + 1) / (past_same + 1))
    q15s = s(q).rolling(15, min_periods=1).sum().values
    F["avg_trade_size"] = np.log(np.maximum(q, 1) / np.maximum(ntr, 1))
    # signed volume (close location value * volume)
    clv = np.where(h > l, (2 * c - h - l) / np.maximum(h - l, 1e-9), 0.0)
    for L in (5, 15, 60):
        F[f"sflow{L}"] = s(clv * q).rolling(L, min_periods=1).sum().values / np.maximum(
            s(q).rolling(L, min_periods=1).sum().values, 1e-9)
    # direction of bar returns weighted by volume
    sgn = np.sign(r1)
    for L in (15, 60):
        F[f"updown{L}"] = s(sgn * q).rolling(L, min_periods=1).sum().values / np.maximum(
            s(q).rolling(L, min_periods=1).sum().values, 1e-9)
    F["clv1"] = clv
    # trend efficiency (|net move| / sum |moves|)
    for L in (15, 60):
        net = np.abs(F[f"r{L}"])
        tot = s(np.abs(r1)).rolling(L, min_periods=1).sum().values
        F[f"eff{L}"] = np.minimum(net / np.maximum(tot, 1.0), 1.0)
    F["dow"] = df["dow"].values.astype(float)
    out = pd.DataFrame(F, index=df.index)
    out = out.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return out
