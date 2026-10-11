"""volume_flow candidate 1: 09:30 US-data-minute volume switch (follow heavy-volume opens, fade light-volume opens).

HIGH OVERFIT RISK: one trade per day, 55 discovery trades, found after a scan over decision times;
the same logic fails at 10:00, 10:30 and 11:00. See DESCRIPTION.
"""
import numpy as np
import pandas as pd

NAME = "volume_flow_0930_volswitch"
DESCRIPTION = (
    "Runs once per day, at the close of the 09:30 one-minute bar. That is the minute of the US 08:30 ET macro "
    "releases (09:30 Brasilia while US daylight time is on). It computes (a) the session move = close of the "
    "09:30 bar minus the open of the session's first bar, and (b) the cumulative contracts traded (qty) from the "
    "session open up to and including the 09:30 bar. (b) is compared with the median of the same 09:30 "
    "cumulative volume over the previous 10 sessions (at least 3 are needed). If volume is at or above that "
    "median, the morning move is treated as information and followed: buy if the move is up, sell if down. If "
    "volume is below the median, the move is treated as noise and faded. Entry is at the open of the 09:31 bar, "
    "with a 500-pt target and a 500-pt stop; any open position is closed at the end of the day. No trade if the "
    "move is exactly zero. Rationale (post hoc): Campbell-Grossman-Wang / Llorente et al., i.e. low-volume "
    "moves revert and high-volume, information-driven moves continue."
)
TARGET = 500
STOP = 500

_DECISION_TIME = 93000   # HHMMSS of the bar whose CLOSE triggers the decision
_LOOKBACK_DAYS = 10
_MIN_DAYS = 3


def signals(df: pd.DataFrame):
    time = df["time"].values
    date = df["date"].values
    qty = df["qty"].values.astype(float)
    opn = df["open"].values
    cls = df["close"].values
    n = len(df)
    if n == 0:
        return []
    starts = np.flatnonzero(np.r_[True, date[1:] != date[:-1]])
    ends = np.r_[starts[1:], n]
    hist = []          # cumulative 09:30 volume of previous sessions (only sessions that have a 09:30 bar)
    out = []
    for s, e in zip(starts, ends):
        pos = np.flatnonzero(time[s:e] == _DECISION_TIME)
        if len(pos) == 0:
            continue
        i = s + int(pos[0])
        cumq = float(qty[s:i + 1].sum())
        move = cls[i] - opn[s]
        prev = hist[-_LOOKBACK_DAYS:]
        if len(prev) >= _MIN_DAYS and move != 0:
            norm = float(np.median(prev))
            d = int(np.sign(move)) if cumq >= norm else -int(np.sign(move))
            out.append((int(i), d))
        hist.append(cumq)
    return out
