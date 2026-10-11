"""Independent re-implementation (no import/copy of wf.py / evaluate.py).

Loader + bracket simulator from the raw CSV, plus the time_of_day_1 rule
implemented from its plain-language description.
"""
import math
import numpy as np
import pandas as pd

CSV = '/home/user/codex-teste/WINFUT_20MB_1.csv'


def load():
    df = pd.read_csv(CSV)
    df.columns = [c.strip('<>') for c in df.columns]
    df = df.sort_values(['date', 'time']).reset_index(drop=True)
    df['hh'] = df.time // 10000
    df['mm'] = (df.time // 100) % 100
    df['mod'] = (df.hh - 9) * 60 + df.mm  # minutes since 09:00
    days = []
    for d, g in df.groupby('date', sort=True):
        g = g.reset_index(drop=True)
        px = np.unique(np.round(np.concatenate([g.open, g.high, g.low, g.close]).astype(float), 6))
        tick = float(np.diff(px).min())
        # sanity: all prices on the day's grid
        k = (px - px.min()) / tick
        assert np.allclose(k, np.round(k), atol=1e-3), d
        days.append(dict(date=int(d), o=g.open.values.astype(float), h=g.high.values.astype(float),
                         l=g.low.values.astype(float), c=g.close.values.astype(float),
                         mod=g['mod'].values.astype(int), time=g.time.values.astype(int), tick=tick))
    return days


def split(days):
    return dict(discovery=days[:59], validation=days[59:79], holdout=days[79:99])


COSTS = {
    'zero': dict(entry_slip=0.0, exit_slip=0.0, fee=0.0, through=0.0),
    'base': dict(entry_slip=1.0, exit_slip=1.0, fee=0.5, through=1.0),
    'stress': dict(entry_slip=2.0, exit_slip=2.0, fee=1.0, through=2.0),
}


def simulate_day(day, sig, target, stop, cost, bracket_from='fill', reentry_same_bar=True,
                 gap_fill=True, last_entry_mod=8 * 60):
    """sig[i] in {+1,-1,0}: decided at close of bar i -> entry at open of bar i+1.
    Returns list of trades (dict)."""
    o, h, l, c, mod, tick = day['o'], day['h'], day['l'], day['c'], day['mod'], day['tick']
    n = len(o)
    es, xs, fee, thr = (cost['entry_slip'] * tick, cost['exit_slip'] * tick,
                        cost['fee'] * tick, cost['through'] * tick)
    trades = []
    i = 0
    free_from = 0  # first bar whose close may generate a new signal
    while i < n - 1:
        if i < free_from or sig[i] == 0:
            i += 1
            continue
        e = i + 1
        if mod[e] > last_entry_mod:  # no entries after 17:00
            i += 1
            continue
        side = sig[i]
        ref = o[e]
        fill = ref + side * es
        anchor = fill if bracket_from == 'fill' else ref
        tgt = anchor + side * target
        stp = anchor - side * stop
        exit_px = None
        reason = None
        j = e
        while j < n:
            if side > 0:
                stop_hit = l[j] <= stp
                tgt_hit = h[j] >= tgt + thr
            else:
                stop_hit = h[j] >= stp
                tgt_hit = l[j] <= tgt - thr
            if stop_hit:  # stop wins ties
                px = stp
                if gap_fill and j > e:
                    # bar opened beyond the stop -> fill at open
                    if (side > 0 and o[j] < stp) or (side < 0 and o[j] > stp):
                        px = o[j]
                exit_px = px - side * xs
                reason = 'stop'
                break
            if tgt_hit:
                px = tgt
                exit_px = px
                reason = 'target'
                break
            if j == n - 1:
                exit_px = c[j] - side * xs
                reason = 'eod'
                break
            j += 1
        pnl = side * (exit_px - fill) - fee
        trades.append(dict(date=day['date'], sig_bar=i, sig_time=int(day['time'][i]), side=side,
                           entry_time=int(day['time'][e]), exit_time=int(day['time'][j]),
                           fill=fill, exit=exit_px, pnl=pnl, reason=reason))
        free_from = j if reentry_same_bar else j + 1
        i = max(i + 1, free_from)
    return trades


def tod_signal(day, start_mod=65, end_mod=89):
    o0 = day['o'][0]
    assert day['time'][0] == 90000
    c, mod = day['c'], day['mod']
    sig = np.zeros(len(c), dtype=int)
    win = (mod >= start_mod) & (mod <= end_mod)
    sig[win & (c > o0)] = -1
    sig[win & (c < o0)] = +1
    return sig


def run(days, cost='base', start_mod=65, end_mod=89, target=500, stop=500, **kw):
    trades = []
    for d in days:
        trades += simulate_day(d, tod_signal(d, start_mod, end_mod), target, stop, COSTS[cost], **kw)
    return trades


def stats(trades, days):
    pnl = np.array([t['pnl'] for t in trades])
    n = len(pnl)
    out = dict(n=n)
    if n == 0:
        return out
    out['avg'] = round(pnl.mean(), 2)
    out['total'] = round(pnl.sum(), 1)
    out['win'] = round((pnl > 0).mean(), 4)
    out['t_trade'] = round(pnl.mean() / (pnl.std(ddof=1) / math.sqrt(n)), 2) if n > 1 else None
    # per-day P&L over all days of the period (zero for days without trades)
    dp = {d['date']: 0.0 for d in days}
    for t in trades:
        dp[t['date']] += t['pnl']
    v = np.array(list(dp.values()))
    out['days'] = len(v)
    out['t_daily_all'] = round(v.mean() / (v.std(ddof=1) / math.sqrt(len(v))), 2)
    traded = sorted({t['date'] for t in trades})
    w = np.array([dp[d] for d in traded])
    out['days_traded'] = len(w)
    out['t_daily_traded'] = round(w.mean() / (w.std(ddof=1) / math.sqrt(len(w))), 2) if len(w) > 1 else None
    out['pct_days_pos'] = round((v > 0).mean(), 3)
    r = [t['reason'] for t in trades]
    out['targets'] = r.count('target'); out['stops'] = r.count('stop'); out['eod'] = r.count('eod')
    out['long_n'] = sum(1 for t in trades if t['side'] > 0)
    out['short_n'] = n - out['long_n']
    return out
