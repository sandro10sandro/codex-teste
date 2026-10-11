import sys, pickle, os
sys.path.insert(0, '/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/lib')
import numpy as np, pandas as pd
import wf
P = os.path.join(os.path.dirname(__file__), 'df.pkl')
def get():
    if os.path.exists(P):
        return pd.read_pickle(P)
    df = wf.load(); df.to_pickle(P); return df

_O = None
def O():
    global _O
    if _O is None:
        _O = pickle.load(open(os.path.join(os.path.dirname(__file__), 'outc.pkl'), 'rb'))
    return _O

def fastbt(df, sigs, T, S, cost='base'):
    """replicates wf.backtest: returns arrays (entry_idx, dir, pnl)"""
    o = O()[(cost, T, S)]
    day = df['day'].values; tm = df['time'].values; n = len(df)
    sigs = sorted({(int(i), int(d)) for i, d in sigs})
    busy = -1; E = []; D = []; Pn = []
    for i, d in sigs:
        e = i + 1
        if e >= n or day[e] != day[i] or tm[e] > 170000 or e <= busy:
            continue
        pnl, ex, kind = o[d]
        E.append(e); D.append(d); Pn.append(pnl[e]); busy = ex[e]
    return np.array(E, int), np.array(D, int), np.array(Pn, float)

NDAYS = 59
def st(df, E, D, Pn):
    if len(Pn) == 0:
        return dict(n=0, total=0, avg=0, t=0, h1=0, h2=0)
    day = df['day'].values[E]
    daily = np.bincount(day, weights=Pn, minlength=NDAYS)
    sd = daily.std(ddof=1)
    t = daily.mean() / (sd / np.sqrt(NDAYS)) if sd > 0 else 0
    half = NDAYS // 2
    return dict(n=len(Pn), total=round(Pn.sum(), 0), avg=round(Pn.mean(), 1), wr=round((Pn > 0).mean(), 3),
                t=round(t, 2), h1=round(daily[:half].sum(), 0), h2=round(daily[half:].sum(), 0))

def scan(df, sigs, cost='base', TS=None):
    TS = TS or [(T, S) for T in (200, 300, 400, 500) for S in (200, 300, 400, 500)]
    res = {}
    for T, S in TS:
        E, D, Pn = fastbt(df, sigs, T, S, cost)
        res[(T, S)] = st(df, E, D, Pn)
    return res
