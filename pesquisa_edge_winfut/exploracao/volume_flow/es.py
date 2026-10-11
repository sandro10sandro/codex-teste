"""Event-study helpers."""
import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/lib')
import numpy as np, pandas as pd
import wf
COUNT_FILE = 'variant_count.txt'

def bump(k):
    try: c = int(open(COUNT_FILE).read().strip())
    except Exception: c = 0
    open(COUNT_FILE,'w').write(str(c+k))
    return c+k

def dedup(idx_dir, F, gap=30):
    """keep events only if no kept event in previous `gap` bars (same day)."""
    out=[]; last=-10**9; lastday=-1
    for i,d in idx_dir:
        if F.day.values[i]==lastday and i-last<gap: continue
        out.append((i,d)); last=i; lastday=F.day.values[i]
    return out

def fwd_study(F, sigs, cols=('fwd15','fwd30','fwd60','L500_500','L300_300')):
    if len(sigs)==0: return None
    idx = np.array([s[0] for s in sigs]); d = np.array([s[1] for s in sigs])
    r = {}
    r['n'] = len(idx)
    day = F.day.values[idx]
    for c in cols:
        if c.startswith('L'):
            x = np.where(d==1, F[c].values[idx], F['S'+c[1:]].values[idx])
        else:
            x = d*F[c].values[idx]
        x = pd.Series(x).fillna(0)
        r[c] = round(x.mean(),1)
        dd = x.groupby(day).sum()
        r[c+'_t'] = round(dd.mean()/(dd.std(ddof=1)/np.sqrt(59)) * np.sqrt(len(dd)/59),2) if len(dd)>2 else np.nan
        r[c+'_h1'] = round(x[day<29].mean(),1); r[c+'_h2'] = round(x[day>=29].mean(),1)
    return r

def bt_grid(df, sigs, combos=None, cost='base'):
    combos = combos or [(t,s) for t in wf.TARGETS for s in wf.STOPS]
    rows=[]
    for t,s in combos:
        tr, st = wf.backtest(df, sigs, t, s, cost)
        if st.get('n',0)==0: continue
        rows.append(dict(T=t,S=s,n=st['n'],tot=st['total'],avg=st['avg'],wr=st['win_rate'],td=st['t_daily'],h1=st['first_half_total'],h2=st['second_half_total']))
    return pd.DataFrame(rows)
