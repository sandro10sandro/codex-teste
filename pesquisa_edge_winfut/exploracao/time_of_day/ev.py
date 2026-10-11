from common import *
import json
TS = [(t, s) for t in (200,300,400,500) for s in (200,300,400,500)]
CNT = os.path.join(HERE, 'count.txt')
def bump(k):
    c = int(open(CNT).read()) if os.path.exists(CNT) else 0
    open(CNT,'w').write(str(c+k))
    return c+k
def ev(df, sig, t, s, cost='base', rb=False):
    tr, st = wf.backtest(df, sig, t, s, cost)
    if st.get('n',0)==0: return dict(n=0)
    out = {k: st.get(k) for k in ('n','total','avg','win_rate','t_daily','first_half_total','second_half_total','pct_days_pos','long_total','short_total','eod')}
    if rb:
        out['p'] = wf.random_baseline(df, tr, t, s, cost)['p_value']
        out['stress'] = wf.backtest(df, sig, t, s, 'stress')[1].get('total')
    return out
def grid(df, sig, cost='base', show=True, label=''):
    rows=[]
    for t,s in TS:
        r = ev(df, sig, t, s, cost); r['t_s']=f'{t}/{s}'; rows.append(r)
    R = pd.DataFrame(rows)
    bump(len(TS))
    if show:
        print(label, R[['t_s','n','total','avg','win_rate','t_daily','first_half_total','second_half_total']].to_string(index=False))
    return R
