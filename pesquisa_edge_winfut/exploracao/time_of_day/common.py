import sys, os, pickle
sys.path.insert(0, '/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/lib')
import numpy as np, pandas as pd
import wf
HERE = os.path.dirname(os.path.abspath(__file__))
PK = os.path.join(HERE, 'disc.pkl')
def get():
    if os.path.exists(PK):
        return pd.read_pickle(PK)
    df = wf.load()
    df.to_pickle(PK)
    return df
