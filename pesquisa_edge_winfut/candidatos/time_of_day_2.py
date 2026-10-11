"""Candidate time_of_day_2 -- single daily fade of the morning move at 10:10 (same effect as time_of_day_1)."""
import numpy as np
import pandas as pd

NAME = "tod_fade_since_open_single_1010"
DESCRIPTION = (
    "Once per day, on the close of the first 1-min bar at or after 10:09 (minutes-since-09:00 >= 69, and "
    "before 10:30), compare that close with today's 09:00 opening price of the future. If price is above "
    "the day open, sell; if below, buy (fade the move made since the open, made mostly before the 10:00 "
    "cash-equity open). Entry at the next bar's open (~10:10), bracket target 500 / stop 500 points, forced "
    "exit at end of day. One trade per day. This is the same hypothesis as time_of_day_1 in its simplest "
    "single-entry form; the two are NOT independent evidence."
)
TARGET = 500
STOP = 500
SIG_MOD = 69     # 10:09 bar close, entry at 10:10 open
LAST_MOD = 90


def signals(df: pd.DataFrame) -> list:
    day = df["day"].to_numpy()
    mod = df["mod"].to_numpy()
    close = df["close"].to_numpy(dtype=float)
    day_open = df.groupby("day")["open"].transform("first").to_numpy(dtype=float)
    out = []
    done = set()
    for i in np.flatnonzero((mod >= SIG_MOD) & (mod < LAST_MOD)):
        d = day[i]
        if d in done:
            continue
        done.add(d)                      # only the first eligible bar of the day
        diff = close[i] - day_open[i]
        if diff > 0:
            out.append((int(i), -1))
        elif diff < 0:
            out.append((int(i), 1))
    return out
