from win import *
from wf import backtest, random_baseline
res = []
for (a, b) in [(0, 80), (0, 90), (0, 100), (15, 90)]:
    for T in (300, 400, 500):
        for S in (300, 400, 500):
            sl, ss, th, models = wf_window(['r_day'], T, S, a, b, qs=(0.75, 0.8, 0.85), C=1.0)
            for q in th:
                sig = make_signals(sl, ss, th, th, 'q', q)
                st = evaluate(sig, T, S)
                tr, _ = backtest(df, sig, T, S, 'base', entry_days=OOS_DATES)
                p = random_baseline(df, tr, T, S, 'base', n_iter=2000, entry_days=OOS_DATES)['p_value']
                res.append(dict(a=a, b=b, T=T, S=S, q=q, p=p, **{k: st.get(k) for k in ('n','total','avg','win_rate','t_daily','first_half_total','second_half_total','stress_total')}))
        print(a, b, flush=True)
R = pd.DataFrame(res); R.to_csv('run7.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
R['pass'] = (R.total > 0) & (R.t_daily >= 2) & (R.n >= 40) & (R.first_half_total > 0) & (R.second_half_total > 0) & (R.p < 0.05) & (R.stress_total > 0)
print(R.pivot_table(index=['a','b','q'], columns=['T','S'], values='t_daily').round(2).to_string())
print(R.pivot_table(index=['a','b','q'], columns=['T','S'], values='second_half_total').round(0).to_string())
print('pass count', R['pass'].sum(), 'of', len(R))
print(R[R['pass']].to_string())
