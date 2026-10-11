"""Candidate time_of_day_1 -- fade the futures-only morning move between the B3 cash open and the US open."""
import numpy as np
import pandas as pd

NAME = "tod_fade_since_open_1005_1030"
DESCRIPTION = (
    "Between 10:05 and 10:29 (signal on the close of each 1-min bar with 65 <= minutes-since-09:00 < 90, "
    "i.e. after the 10:00 cash-equity open has settled and before the 10:30 US cash open), compare the bar "
    "close with today's 09:00 opening price of the future. If price is above the day open, sell; if below, "
    "buy (fade the move made since the open, which in 2012 was made mostly while only futures traded). "
    "Entry at the next bar's open, one position at a time (re-entry allowed while still inside the window), "
    "bracket target 500 / stop 500 points, forced exit at end of day. No other filters."
)
TARGET = 500
STOP = 500
START_MOD = 65   # 10:05 signal bar
END_MOD = 90     # last signal bar is 10:29 (entry 10:30)


def signals(df: pd.DataFrame) -> list:
    day = df["day"].to_numpy()
    mod = df["mod"].to_numpy()
    close = df["close"].to_numpy(dtype=float)
    day_open = df.groupby("day")["open"].transform("first").to_numpy(dtype=float)
    idx = np.flatnonzero((mod >= START_MOD) & (mod < END_MOD))
    out = []
    for i in idx:
        diff = close[i] - day_open[i]
        if diff > 0:
            out.append((int(i), -1))
        elif diff < 0:
            out.append((int(i), 1))
    return out
