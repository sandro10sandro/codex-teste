import sys, pickle, os
sys.path.insert(0, '/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/lib')
import numpy as np, pandas as pd
from wf import load, backtest, random_baseline, lookahead_check, outcomes, stats
HERE = os.path.dirname(os.path.abspath(__file__))
_df = None
def get_df():
    global _df
    if _df is None:
        p = os.path.join(HERE, 'df.pkl')
        if os.path.exists(p):
            _df = pd.read_pickle(p)
        else:
            _df = load(); _df.to_pickle(p)
    return _df
