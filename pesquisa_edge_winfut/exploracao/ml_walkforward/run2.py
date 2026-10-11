from sym import *
import time
ALLS = SIGNED + ['d_high','d_low','d_prevhigh','d_prevlow'] + UNSIGNED + POS
res = []; t0 = time.time()
configs = [('lr', dict(C=0.01)), ('lr', dict(C=1.0)), ('hgb', dict(depth=3, iters=100, leaf=400)), ('hgb', dict(depth=2, iters=50, leaf=1000)),
           ('ridge', dict(alpha=1000.0))]
for kind, kw in configs:
    for T, S in [(500, 500), (300, 300), (500, 300), (300, 500), (400, 400)]:
        sl, ss, thl, ths, _ = wf_sym(ALLS, T, S, kind, sub=2, **kw)
        for q in (0.90, 0.95, 0.98):
            st = evaluate(make_signals(sl, ss, thl, ths, 'q', q), T, S)
            res.append(dict(kind=kind, kw=str(kw), T=T, S=S, q=q, **{k: st.get(k) for k in ('n','total','avg','win_rate','t_daily','first_half_total','second_half_total','stress_total','long_n','long_total','short_n','short_total')}))
        print(kind, kw, T, S, round(time.time()-t0), flush=True)
R = pd.DataFrame(res); R.to_csv('run2.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
print(R.sort_values('t_daily', ascending=False).to_string())
