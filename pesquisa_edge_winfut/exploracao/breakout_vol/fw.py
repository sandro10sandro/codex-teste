import sys, os, time
sys.path.insert(0, '/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/lib')
import numpy as np, pandas as pd
import wf
from wf import load, backtest, random_baseline, lookahead_check, outcomes, stats

TS = [(t, s) for t in (200, 300, 400, 500) for s in (200, 300, 400, 500)]
VARIANTS = [0]

_df = None
def get_df():
    global _df
    if _df is None:
        _df = load()
    return _df

def fast_bt(df, sigs, target, stop, cost='base'):
    """same logic as wf.backtest, returns arrays (entry idx, dir, pnl, date)"""
    out = outcomes(df, target, stop, cost)
    day = df['day'].values; tm = df['time'].values; n = len(df)
    sigs = sorted({(int(i), int(d)) for i, d in sigs if d in (1, -1)})
    E, D, P = [], [], []
    busy = -1
    for i, d in sigs:
        e = i + 1
        if e >= n or day[e] != day[i] or tm[e] > 170000 or e <= busy:
            continue
        pnl, ex, kind = out[d]
        E.append(e); D.append(d); P.append(pnl[e]); busy = ex[e]
    return np.array(E, int), np.array(D, int), np.array(P, float)

def quick_stats(df, E, D, P):
    n = len(P)
    if n == 0:
        return dict(n=0, total=0, t=0, h1=0, h2=0, avg=0, wr=0)
    days = df['day'].values
    nd = days.max() + 1
    daily = np.bincount(days[E], weights=P, minlength=nd)
    half = nd // 2
    sd = daily.std(ddof=1)
    t = daily.mean() / (sd / np.sqrt(nd)) if sd > 0 else 0
    return dict(n=n, total=round(P.sum(), 0), avg=round(P.mean(), 1), wr=round((P > 0).mean(), 3),
                t=round(t, 2), h1=round(daily[:half].sum(), 0), h2=round(daily[half:].sum(), 0),
                L=int((D == 1).sum()), Ltot=round(P[D == 1].sum(), 0), S=int((D == -1).sum()), Stot=round(P[D == -1].sum(), 0))

def grid(df, sigs, ts=TS, cost='base', count=True):
    rows = []
    for t, s in ts:
        E, D, P = fast_bt(df, sigs, t, s, cost)
        st = quick_stats(df, E, D, P); st['T'] = t; st['S_'] = s
        rows.append(st)
        if count: VARIANTS[0] += 1
    return pd.DataFrame(rows)

def passes(st):
    return st['n'] >= 40 and st['total'] > 0 and st['t'] >= 2 and st['h1'] > 0 and st['h2'] > 0

def full_check(df, sigs, t, s, fn=None):
    tr, st = backtest(df, sigs, t, s, 'base')
    rb = random_baseline(df, tr, t, s, 'base')
    tr2, st2 = backtest(df, sigs, t, s, 'stress')
    res = dict(st); res['p'] = rb['p_value']; res['stress_total'] = st2.get('total')
    if fn is not None:
        res['lookahead'] = lookahead_check(fn, df)
    return res
