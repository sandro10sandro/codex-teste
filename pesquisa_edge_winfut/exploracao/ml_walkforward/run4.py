from ic import *
import time
res=[]
sets = {'gap_zday': ['gap','z_day'], 'gap_rday': ['gap','r_day'], 'zday': ['z_day'], 'gap_zday_prevc': ['gap','z_day','d_prevclose'],
        'gap_zday_zvwap': ['gap','z_day','z_vwap']}
for name, cols in sets.items():
    for T,S in [(500,500),(400,400),(300,300),(300,500),(500,300)]:
        sl, ss, thl, ths, models = wf_sym(cols, T, S, 'lr', sub=1, C=1.0)
        icv = oos_ic(sl, ss, T, S)
        for q in (0.90,0.95,0.98):
            st = evaluate(make_signals(sl, ss, thl, ths, 'q', q), T, S)
            res.append(dict(set=name, T=T, S=S, q=q, ic=icv[0], ic_t=icv[1], **{k: st.get(k) for k in ('n','total','avg','win_rate','t_daily','first_half_total','second_half_total','stress_total','long_n','short_n')}))
        print(name, T, S, icv, [np.round(m.coef_[0],3) for _,m,_ in models[::3]], flush=True)
R=pd.DataFrame(res); R.to_csv('run4.csv',index=False)
pd.set_option('display.width',250); pd.set_option('display.max_rows',500)
print(R.sort_values('t_daily',ascending=False).head(30).to_string())
