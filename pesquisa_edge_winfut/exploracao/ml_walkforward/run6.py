from win import *
res = []
sets = {'rday': ['r_day'], 'zday': ['z_day'], 'rday_gap': ['r_day', 'gap'], 'rday_prevhl': ['r_day', 'd_prevhigh'], 'rday_vwap': ['r_day','z_vwap']}
for name, cols in sets.items():
    for T, S in [(500, 500), (400, 400), (300, 300), (300, 500), (500, 300)]:
        sl, ss, th, models = wf_window(cols, T, S, 0, 90, C=1.0)
        icv = oos_ic(sl, ss, T, S)
        for q in th:
            st = evaluate(make_signals(sl, ss, th, th, 'q', q), T, S)
            res.append(dict(set=name, T=T, S=S, q=q, ic=icv[0], ic_t=icv[1], **{k: st.get(k) for k in ('n','total','avg','win_rate','t_daily','first_half_total','second_half_total','stress_total','long_n','short_n')}))
        print(name, T, S, icv[:2], [np.round(m.coef_[0], 3) for _, m, _ in models[::3]], flush=True)
R = pd.DataFrame(res); R.to_csv('run6.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
print(R.sort_values('t_daily', ascending=False).to_string())
