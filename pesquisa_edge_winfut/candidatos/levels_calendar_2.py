"""levels_calendar candidate 2: break of a stale day high/low, read through the prior close (day-type conditional).
NOTE: same underlying idea as levels_calendar_1 (daily P&L correlation ~0.55) - not independent evidence."""
import numpy as np
import pandas as pd

NAME = "levels_calendar_2_pdc_conditional_stale_extreme_break"
DESCRIPTION = (
    "Reference levels: yesterday's last close (PDC) and today's running high/low. When a bar CLOSES above the "
    "day's high so far and that high had stood for at least 30 bars (minutes), or closes below the day's low so "
    "far that had stood for at least 30 bars, that is a break of a stale extreme (can occur several times a day). "
    "At that bar, check whether the price has traded at PDC at any time since today's open (gap filled -> "
    "two-sided/balanced day). If the gap is filled, FADE the break (short new highs, buy new lows). If the gap is "
    "still open (one-sided day), FOLLOW the break. Entry at the next bar's open, target 400 pts, stop 500 pts "
    "(adjusted-series points), library rules (one position at a time, no entries after 17:00, flat at the last bar)."
)
TARGET = 400
STOP = 500
STALE_BARS = 30


def signals(df: pd.DataFrame):
    o = df["open"].to_numpy(float)
    h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float)
    c = df["close"].to_numpy(float)
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
        H, L = h[s], l[s]
        tH = tL = s
        for j in range(s + 1, e):
            run_hi = max(H, h[j])
            run_lo = min(L, l[j])
            filled = (dopen >= pdc and run_lo <= pdc) or (dopen <= pdc and run_hi >= pdc)
            if c[j] > H and j - tH >= STALE_BARS:
                out.append((int(idx_all[j]), -1 if filled else 1))
            if c[j] < L and j - tL >= STALE_BARS:
                out.append((int(idx_all[j]), 1 if filled else -1))
            if h[j] > H:
                H, tH = h[j], j
            if l[j] < L:
                L, tL = l[j], j
    return out
