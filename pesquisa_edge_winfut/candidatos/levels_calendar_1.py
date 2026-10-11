"""levels_calendar candidate 1: 10:00 range break, read through the prior close (day-type conditional)."""
import numpy as np
import pandas as pd

NAME = "levels_calendar_1_pdc_conditional_10h_range_break"
DESCRIPTION = (
    "Reference levels: yesterday's last close (PDC) and the 09:00-09:59 range (the futures-only hour before "
    "the 10:00 cash-equity open). From 10:00 on, take the FIRST bar whose close is at/above the 9h range high "
    "(previous close below it) and the FIRST bar whose close is at/below the 9h range low (previous close above "
    "it); at most one up-break and one down-break per day. At that bar, check whether the price has traded at "
    "PDC at any time since today's open (gap already filled -> two-sided/balanced day). If the gap is filled, "
    "FADE the break (short an up-break, buy a down-break). If the gap is still open (one-sided day), FOLLOW the "
    "break. Entry at the next bar's open, target 300 pts, stop 500 pts (adjusted-series points), library rules "
    "(one position at a time, no entries after 17:00, flat at the last bar)."
)
TARGET = 300
STOP = 500
OR_MINUTES = 60   # 09:00-09:59 = pre-cash-open range


def signals(df: pd.DataFrame):
    o = df["open"].to_numpy(float)
    h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float)
    c = df["close"].to_numpy(float)
    mod = df["mod"].to_numpy()
    day = df["day"].to_numpy()
    idx_all = df.index.to_numpy()
    n = len(df)
    if n == 0:
        return []
    starts = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
    ends = np.r_[starts[1:], n]
    out = []
    prev_close = np.nan
    for s, e in zip(starts, ends):
        pdc = prev_close
        prev_close = c[e - 1]
        if np.isnan(pdc):
            continue
        dopen = o[s]
        orh = -np.inf
        orl = np.inf
        run_hi = -np.inf
        run_lo = np.inf
        du = dn = False
        for j in range(s, e):
            run_hi = max(run_hi, h[j])
            run_lo = min(run_lo, l[j])
            if mod[j] < OR_MINUTES:
                orh = max(orh, h[j])
                orl = min(orl, l[j])
                continue
            if not np.isfinite(orh) or j == s:
                continue
            filled = (dopen >= pdc and run_lo <= pdc) or (dopen <= pdc and run_hi >= pdc)
            if (not du) and c[j] >= orh and c[j - 1] < orh:
                du = True
                out.append((int(idx_all[j]), -1 if filled else 1))
            if (not dn) and c[j] <= orl and c[j - 1] > orl:
                dn = True
                out.append((int(idx_all[j]), 1 if filled else -1))
    return out
