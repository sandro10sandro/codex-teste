from ic import *
modv = df['mod'].values
def wf_window(cols, T, S, a, b, kind='lr', qs=(0.8, 0.9, 0.95), min_train=MIN_TRAIN, step=STEP, label='pnl', **kw):
    yl, ys = labels(T, S)
    wmask = (modv >= a) & (modv < b)
    XL = aligned(cols, 1); XS = aligned(cols, -1)
    sl = np.full(n, np.nan); ss = np.full(n, np.nan); th = {q: np.full(n, np.nan) for q in qs}
    typ, mk = make_model(kind, **kw)
    models = []
    for start in range(min_train, len(DATES), step):
        idx = np.flatnonzero(valid & wmask & (day < start))
        te = wmask & (day >= start) & (day < start + step)
        Xtr = np.vstack([XL[idx], XS[idx]]); ytr = np.r_[yl[idx], ys[idx]] > 0
        sc = StandardScaler().fit(Xtr); m = mk(); m.fit(sc.transform(Xtr), ytr)
        ptr = m.predict_proba(sc.transform(Xtr))[:, 1]
        sl[te] = m.predict_proba(sc.transform(XL[te]))[:, 1]; ss[te] = m.predict_proba(sc.transform(XS[te]))[:, 1]
        for q in qs: th[q][te] = np.quantile(ptr, q)
        models.append((start, m, sc))
    return sl, ss, th, models
