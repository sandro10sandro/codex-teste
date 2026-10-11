from wfml import *
import itertools, json, time
ALL = list(F.columns)
res = []
t0 = time.time()
configs = [('lr', dict(C=0.01)), ('lr', dict(C=1.0)), ('tree', dict(depth=3, leaf=800)), ('hgb', dict(depth=3, iters=100, leaf=400)),
           ('ridge', dict(alpha=1000.0)), ('hgbr', dict(depth=3, iters=100, leaf=400))]
for (kind, kw) in configs:
    for T, S in [(500, 500), (300, 300), (500, 300), (300, 500), (200, 200), (400, 400)]:
        sl, ss, thl, ths = wf_scores(ALL, T, S, kind, sub=2, **kw)
        for q in (0.90, 0.95, 0.98):
            st = evaluate(make_signals(sl, ss, thl, ths, 'q', q), T, S)
            res.append(dict(kind=kind, kw=str(kw), T=T, S=S, mode='q', q=q, **{k: st.get(k) for k in ('n','total','avg','win_rate','t_daily','first_half_total','second_half_total','stress_total','long_n','long_total','short_n','short_total')}))
        if kind in ('ridge', 'hgbr'):
            for mg in (0.0, 20.0):
                st = evaluate(make_signals(sl, ss, thl, ths, 'abs', margin=mg), T, S)
                res.append(dict(kind=kind, kw=str(kw), T=T, S=S, mode='abs', q=mg, **{k: st.get(k) for k in ('n','total','avg','win_rate','t_daily','first_half_total','second_half_total','stress_total','long_n','long_total','short_n','short_total')}))
        print(kind, kw, T, S, round(time.time()-t0), flush=True)
R = pd.DataFrame(res)
R.to_csv('run1.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
print(R.sort_values('t_daily', ascending=False).to_string())
