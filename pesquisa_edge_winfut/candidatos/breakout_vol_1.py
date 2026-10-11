"""Candidate breakout_vol_1 -- fade the first break of the 30-minute opening range,
only when that break happens before the cash-equity open (10:00).

Discovery period only (2012-05-02..2012-07-25). See DESCRIPTION.
"""
import numpy as np
import pandas as pd

NAME = "OR30 first-break fade before cash open"
DESCRIPTION = (
    "Opening range = high and low of the first 30 minutes of the WIN session (bars 09:00-09:29). "
    "From 09:30 on, find the FIRST 1-minute bar of the day whose close is outside that range "
    "(above the high or below the low). If that bar closes at or before 09:59 (i.e. before the "
    "Bovespa cash-equity market opens at 10:00), trade AGAINST the break at the open of the next bar: "
    "close above the range high -> sell; close below the range low -> buy. At most one trade per day; "
    "if the first break happens at 10:00 or later there is no trade that day. "
    "Fixed bracket: target 500 pts, stop 500 pts (adjusted-series points), else exit at day end. "
    "Rationale: before the cash market opens the future trades thin and without the equity flow, so "
    "the first escape from the early range tends to be a fake-out that reverts. "
    "Free choices: opening-range length (30 min), the 10:00 cutoff (cash open), bracket 500/500."
)
TARGET = 500
STOP = 500

OR_MINUTES = 30      # opening range = bars with mod < 30
LAST_SIGNAL_MOD = 59  # signal bar must be at or before 09:59 (mod <= 59)


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
            if m[k] > LAST_SIGNAL_MOD:
                break
            i = s + k
            if c[i] > orh:
                out.append((int(i), -1))
                break
            if c[i] < orl:
                out.append((int(i), 1))
                break
    return out
