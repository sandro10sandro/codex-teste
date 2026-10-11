from fwd import *
import time
ALLS = SIGNED + ['d_high','d_low','d_prevhigh','d_prevlow'] + UNSIGNED + POS
res = []; t0 = time.time()
for H in (10, 30, 60):
    y = fwd_ret(H)
    yv = y / np.maximum(F['vol60'].values, 1.0)  # vol-normalized
    for kind, kw in [('ridge', dict(alpha=1000.0)), ('hgbr', dict(depth=3, iters=100, leaf=400))]:
        sl, ss, th = wf_sym_y(ALLS, yv, kind, **kw)
        icv = ic_fwd(sl, y)
        for T, S in [(300, 300), (400, 400), (500, 500), (300, 500), (500, 300)]:
            for q in (0.90, 0.95, 0.98):
                st = evaluate(make_signals(sl, ss, th, th, 'q', q), T, S)
                res.append(dict(H=H, kind=kind, ic=icv[0], ic_t=icv[1], T=T, S=S, q=q, **{k: st.get(k) for k in ('n','total','avg','win_rate','t_daily','first_half_total','second_half_total','stress_total')}))
        print(H, kind, icv, round(time.time()-t0), flush=True)
R = pd.DataFrame(res); R.to_csv('run3.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
print(R.sort_values('t_daily', ascending=False).head(40).to_string())
print(R.groupby(['H','kind'])[['avg','t_daily']].mean())
