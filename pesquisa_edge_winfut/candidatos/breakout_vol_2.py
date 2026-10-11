"""Candidate breakout_vol_2 -- fade the first break of the 30-minute opening range (any time).

Same hypothesis as breakout_vol_1 without the 10:00 cutoff (strictly 3 free parameters).
Discovery period only (2012-05-02..2012-07-25). See DESCRIPTION.
"""
import numpy as np
import pandas as pd

NAME = "OR30 first-break fade (any time)"
DESCRIPTION = (
    "Opening range = high and low of the first 30 minutes of the WIN session (bars 09:00-09:29). "
    "From 09:30 on, find the FIRST 1-minute bar of the day whose close is outside that range. "
    "Trade AGAINST that break at the open of the next bar: close above the range high -> sell; "
    "close below the range low -> buy. Exactly one signal per day (the first break, whenever it happens; "
    "the library blocks entries after 17:00). Fixed bracket: target 500 pts, stop 500 pts, else exit at "
    "day end. Same hypothesis as breakout_vol_1 (early-range fake-outs revert) but without the "
    "cash-open cutoff; about 75% of its trades are the same trades. "
    "Free choices: opening-range length (30 min), target 500, stop 500."
)
TARGET = 500
STOP = 500

OR_MINUTES = 30


def signals(df):
    mod = df["mod"].to_numpy()
    h = df["high"].to_numpy(dtype=float)
    l = df["low"].to_numpy(dtype=float)
    c = df["close"].to_numpy(dtype=float)
    day = df["day"].to_numpy()
    n = len(df)
    if n == 0:
        return []
    starts = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
    ends = np.r_[starts[1:], n]
    out = []
    for s, e in zip(starts, ends):
        m = mod[s:e]
        in_or = m < OR_MINUTES
        if not in_or.any():
            continue
        orh = h[s:e][in_or].max()
        orl = l[s:e][in_or].min()
        for k in np.flatnonzero(m >= OR_MINUTES):
            i = s + k
            if c[i] > orh:
                out.append((int(i), -1))
                break
            if c[i] < orl:
                out.append((int(i), 1))
                break
    return out
