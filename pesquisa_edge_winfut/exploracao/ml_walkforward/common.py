import sys
sys.path.insert(0, '/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/lib')
import numpy as np, pandas as pd
from wf import outcomes, backtest, random_baseline, NO_ENTRY_AFTER

df = pd.read_pickle('/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/logs/ml_walkforward/disc.pkl')
F = pd.read_pickle('/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/logs/ml_walkforward/F.pkl')
n = len(df)
day = df['day'].values
tm = df['time'].values
# signal bar i valid if entry bar i+1 in same day and <= 17:00
valid = np.zeros(n, bool)
valid[:-1] = (day[1:] == day[:-1]) & (tm[1:] <= NO_ENTRY_AFTER)

def labels(T, S, cost='base'):
    out = outcomes(df, T, S, cost)
    yl = np.full(n, np.nan); ys = np.full(n, np.nan)
    yl[:-1] = out[1][0][1:]; ys[:-1] = out[-1][0][1:]
    yl[~valid] = np.nan; ys[~valid] = np.nan
    return yl, ys
