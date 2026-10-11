from ic import *
import time
ALLS = SIGNED + ['d_high','d_low','d_prevhigh','d_prevlow'] + UNSIGNED + POS
modv = df['mod'].values
windows = {'w0900_1030': (0, 90), 'w1030_1200': (90, 180), 'w1200_1500': (180, 360), 'w1500_1700': (360, 481)}
res = []
for wname, (a, b) in windows.items():
    wmask = (modv >= a) & (modv < b)
    for T, S in [(500, 500), (300, 300)]:
        yl, ys = labels(T, S)
        for kind, kw in [('lr', dict(C=0.01)), ('hgb', dict(depth=2, iters=60, leaf=300))]:
            XL = aligned(ALLS, 1); XS = aligned(ALLS, -1)
            sl = np.full(n, np.nan); ss = np.full(n, np.nan); th = {q: np.full(n, np.nan) for q in (0.9, 0.95)}
            typ, mk = make_model(kind, **kw)
            for start in range(MIN_TRAIN, len(DATES), STEP):
                idx = np.flatnonzero(valid & wmask & (day < start))
                te = wmask & (day >= start) & (day < start + STEP)
                Xtr = np.vstack([XL[idx], XS[idx]]); ytr = np.r_[yl[idx], ys[idx]] > 0
                sc = StandardScaler().fit(Xtr); m = mk(); m.fit(sc.transform(Xtr), ytr)
                ptr = m.predict_proba(sc.transform(Xtr))[:, 1]
                sl[te] = m.predict_proba(sc.transform(XL[te]))[:, 1]; ss[te] = m.predict_proba(sc.transform(XS[te]))[:, 1]
                for q in th: th[q][te] = np.quantile(ptr, q)
            icv = oos_ic(sl, ss, T, S)
            for q in th:
                st = evaluate(make_signals(sl, ss, th, th, 'q', q), T, S)
                res.append(dict(win=wname, T=T, S=S, kind=kind, q=q, ic=icv[0], ic_t=icv[1], **{k: st.get(k) for k in ('n','total','avg','win_rate','t_daily','first_half_total','second_half_total','stress_total')}))
            print(wname, T, S, kind, icv, flush=True)
R = pd.DataFrame(res); R.to_csv('run5.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
print(R.sort_values('t_daily', ascending=False).head(20).to_string())
