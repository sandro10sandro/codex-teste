from sym import *
from scipy.stats import spearmanr
c = df['close'].values; o = df['open'].values
def fwd_ret(H):
    """return from open of bar i+1 to close of bar min(i+H, last bar of day), in bp. Label for signal bar i."""
    s = pd.Series
    last_idx = s(np.arange(n)).groupby(day).transform('max').values
    j = np.minimum(np.arange(n) + H, last_idx)
    e = np.minimum(np.arange(n) + 1, n - 1)
    r = (np.log(c[j]) - np.log(o[e])) * 1e4
    r[~valid] = np.nan
    return r

def wf_sym_y(cols, y_long, kind, sub=2, qs=(0.90, 0.95, 0.98), clf=False, **kw):
    XL = aligned(cols, 1); XS = aligned(cols, -1)
    sl = np.full(n, np.nan); ss = np.full(n, np.nan)
    th = {q: np.full(n, np.nan) for q in qs}
    typ, mk = make_model(kind, **kw)
    for start in range(MIN_TRAIN, len(DATES), STEP):
        idx = np.flatnonzero(valid & (day < start) & ~np.isnan(y_long))[::sub]
        te = (day >= start) & (day < start + STEP)
        Xtr = np.vstack([XL[idx], XS[idx]]); ytr = np.r_[y_long[idx], -y_long[idx]]
        sc = StandardScaler().fit(Xtr)
        m = mk()
        if typ == 'clf':
            m.fit(sc.transform(Xtr), (ytr > 0).astype(int)); f = lambda X: m.predict_proba(sc.transform(X))[:, 1]
        else:
            m.fit(sc.transform(Xtr), ytr); f = lambda X: m.predict(sc.transform(X))
        ptr = f(Xtr)
        sl[te] = f(XL[te]); ss[te] = f(XS[te])
        for q in qs:
            th[q][te] = np.quantile(ptr, q)
    return sl, ss, th

def ic_fwd(sl, y):
    m = valid & ~np.isnan(sl) & ~np.isnan(y)
    ics = np.array([spearmanr(sl[m & (day == k)], y[m & (day == k)]).correlation for k in np.unique(day[m])])
    return round(np.nanmean(ics), 4), round(np.nanmean(ics) / (np.nanstd(ics) / np.sqrt(len(ics))), 2)
