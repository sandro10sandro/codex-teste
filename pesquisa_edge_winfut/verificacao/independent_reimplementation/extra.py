from sim import *
import numpy as np, math
rng=np.random.default_rng(12345)
days=load(); P=split(days)
P['oos']=P['validation']+P['holdout']

def tstat(v):
    v=np.asarray(v,float); return v.mean()/(v.std(ddof=1)/math.sqrt(len(v)))

print('== Path-independent fade (one per day): signal at 10:05 close vs 09:00 open, enter 10:06 open, exit at close of bar T; points; no costs')
for per in ['discovery','validation','holdout','oos']:
    row=[]
    for T in [90,120,180,300,509]:  # 10:30, 11:00, 12:00, 14:00, 17:29
        r=[]
        for d in P[per]:
            mod=d['mod']
            if 65 not in mod or T not in mod: continue
            i=int(np.where(mod==65)[0][0]); j=int(np.where(mod==T)[0][0])
            s=-np.sign(d['c'][i]-d['o'][0])
            if s==0: continue
            r.append(s*(d['c'][j]-d['o'][i+1]))
        row.append(f"T={9+T//60:02d}:{T%60:02d} n={len(r)} mean={np.mean(r):7.1f} t={tstat(r):5.2f}")
    print(per.ljust(10),' | '.join(row))

print()
print('== Daily direction-flip randomization (flip all of a day\'s signals w.p. 0.5), time_of_day_1 500/500')
def daily_pnl(dayset,cost,flips=None):
    out=[]
    for k,d in enumerate(dayset):
        s=tod_signal(d)
        if flips is not None and flips[k]: s=-s
        out.append(sum(t['pnl'] for t in simulate_day(d,s,500,500,COSTS[cost])))
    return np.array(out)
for per in ['validation','holdout','oos']:
    for cost in ['zero','base']:
        act=daily_pnl(P[per],cost).sum()
        sims=np.array([daily_pnl(P[per],cost,rng.random(len(P[per]))<0.5).sum() for _ in range(1000)])
        print(f"{per:10s} {cost:4s} actual={act:8.1f} rand_mean={sims.mean():8.1f} p(one-sided)={(sims>=act).mean():.3f}")

print()
print('== Power: daily P&L SD and t expected under shrunk true edge (base costs)')
dd=daily_pnl(P['discovery'],'base'); dv=daily_pnl(P['validation'],'base'); dh=daily_pnl(P['holdout'],'base')[:19]
print('discovery daily mean %.1f sd %.1f; validation mean %.1f sd %.1f; holdout(19 tradable days) mean %.1f sd %.1f'%(dd.mean(),dd.std(ddof=1),dv.mean(),dv.std(ddof=1),dh.mean(),dh.std(ddof=1)))
sd=np.concatenate([dv,dh]).std(ddof=1)
from math import erf,sqrt
Phi=lambda x:0.5*(1+erf(x/sqrt(2)))
for frac in [1.0,0.5,0.33,0.25]:
    mu=dd.mean()*frac
    for n in [19,39]:
        et=mu/(sd/math.sqrt(n))
        # P(t>1.645) approx normal
        print(f"true daily edge = {frac:.2f} x discovery ({mu:6.1f}/day), n_days={n}: expected t={et:4.2f}, power(one-sided 5%)~{1-Phi(1.645-et):.2f}")
