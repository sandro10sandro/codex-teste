from sim import *
days=load(); P=split(days)
P['oos']=P['validation']+P['holdout']
print('window shift sensitivity (start..end inclusive), 500/500')
for sh in [-10,-5,0,5,10]:
    s0,e0=65+sh,89+sh
    lab=f"{9+s0//60:02d}:{s0%60:02d}-{9+e0//60:02d}:{e0%60:02d}"
    for per in ['discovery','validation','holdout','oos']:
        for cost in ['zero','base']:
            if per!='oos' and cost=='base': continue
            s=stats(run(P[per],cost,s0,e0),P[per])
            print(f"shift {sh:+3d} {lab} {per:10s} {cost:4s} n={s['n']:3d} avg={s['avg']:7.1f} tot={s['total']:8.0f} win={s['win']:.3f} T/S={s['targets']}/{s['stops']} t_daily={s['t_daily_all']:5.2f}")
    print()
