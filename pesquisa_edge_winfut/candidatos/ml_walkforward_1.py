"""ml_walkforward candidate 1: opening-session fade-to-open logistic model (frozen).

Research: scratchpad/edge/logs/ml_walkforward/ (run5.py found the opening-window effect, run6/run7.py walk-forward).
Model: direction-symmetric logistic regression, trained on the pooled long+short samples of
bars 09:00-10:29, label = (400/400 bracket trade with base costs ends with profit), one feature:
the direction-aligned return since the day's open (bp). Frozen on all 59 discovery days.
"""
import numpy as np
import pandas as pd

NAME = "ml_wf_open_fade_lr"
DESCRIPTION = (
    "Opening-session fade toward the day's open, chosen by a walk-forward logistic model. "
    "For each 1-minute bar from 09:00 to 10:29, compute r = log(close / first open of the day) in basis points. "
    "A frozen direction-symmetric logistic regression gives P(win) for a long (feature +r) and for a short "
    "(feature -r); a trade is signalled when P(win) exceeds the 80th percentile of its training predictions. "
    "In practice: if price is more than about 32 bp (~0.32%) ABOVE the day's open, sell; if more than about "
    "32 bp BELOW the open, buy (bet on reversion toward the open before the US cash open at 10:30 BRT). "
    "Entry at next bar open, target 400 / stop 400 points, one position at a time, forced exit at end of day."
)
TARGET = 400
STOP = 400

# frozen logistic model (trained on all discovery days, sklearn LogisticRegression C=1.0 on standardized feature)
A = -0.09564722067201777      # intercept
B = -0.3659444278186187       # coefficient on standardized aligned r_day
MU = 0.0                      # scaler mean (pooled long/short -> symmetric, ~0)
SD = 45.624920966072494       # scaler std (bp)
THR = 0.5400857162472631      # 80th percentile of training predicted probabilities
WINDOW_END_MOD = 90           # minutes after 09:00 (signals only on bars 09:00..10:29)


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def signals(df: pd.DataFrame):
    c = df["close"].values.astype(float)
    o = df["open"].values.astype(float)
    day = df["day"].values
    mod = df["mod"].values
    dopen = pd.Series(o).groupby(day).transform("first").values
    r_day = (np.log(c) - np.log(dopen)) * 1e4
    p_long = _sigmoid(A + B * (r_day - MU) / SD)
    p_short = _sigmoid(A + B * (-r_day - MU) / SD)
    win = mod < WINDOW_END_MOD
    out = []
    for i in np.flatnonzero(win & ((p_long > THR) | (p_short > THR))):
        out.append((int(i), 1 if p_long[i] >= p_short[i] else -1))
    return out
