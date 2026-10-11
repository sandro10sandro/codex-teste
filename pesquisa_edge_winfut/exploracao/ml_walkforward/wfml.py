from common import *
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import warnings; warnings.filterwarnings('ignore')

DATES = np.array(sorted(df['date'].unique()))
MIN_TRAIN, STEP = 20, 5

def make_model(kind, **kw):
    if kind == 'lr':
        return ('clf', lambda: LogisticRegression(C=kw.get('C', 0.1), max_iter=500))
    if kind == 'tree':
        return ('clf', lambda: DecisionTreeClassifier(max_depth=kw.get('depth', 3), min_samples_leaf=kw.get('leaf', 500)))
    if kind == 'hgb':
        return ('clf', lambda: HistGradientBoostingClassifier(max_depth=kw.get('depth', 3), max_iter=kw.get('iters', 100),
                learning_rate=0.05, min_samples_leaf=kw.get('leaf', 300), l2_regularization=1.0))
    if kind == 'ridge':
        return ('reg', lambda: Ridge(alpha=kw.get('alpha', 100.0)))
    if kind == 'treg':
        return ('reg', lambda: DecisionTreeRegressor(max_depth=kw.get('depth', 3), min_samples_leaf=kw.get('leaf', 500)))
    if kind == 'hgbr':
        return ('reg', lambda: HistGradientBoostingRegressor(max_depth=kw.get('depth', 3), max_iter=kw.get('iters', 100),
                learning_rate=0.05, min_samples_leaf=kw.get('leaf', 300), l2_regularization=1.0))

def wf_scores(cols, T, S, kind, sub=1, **kw):
    """Walk-forward OOS scores for long and short. Returns (score_long, score_short, thr_long, thr_short dict per quantile)."""
    yl, ys = labels(T, S)
    X = F[cols].values
    sl = np.full(n, np.nan); ss = np.full(n, np.nan)
    thr = {}  # per bar: training-quantile thresholds
    typ, mk = make_model(kind, **kw)
    qs = (0.80, 0.90, 0.95, 0.98)
    thl = {q: np.full(n, np.nan) for q in qs}; ths = {q: np.full(n, np.nan) for q in qs}
    for start in range(MIN_TRAIN, len(DATES), STEP):
        tr = valid & (day < start)
        idx = np.flatnonzero(tr)[::sub]
        te = (day >= start) & (day < start + STEP)
        sc = StandardScaler().fit(X[idx])
        Xtr = sc.transform(X[idx]); Xte = sc.transform(X[te])
        for y, out, th in ((yl, sl, thl), (ys, ss, ths)):
            m = mk()
            if typ == 'clf':
                m.fit(Xtr, (y[idx] > 0).astype(int))
                ptr = m.predict_proba(Xtr)[:, 1]; pte = m.predict_proba(Xte)[:, 1]
            else:
                m.fit(Xtr, y[idx])
                ptr = m.predict(Xtr); pte = m.predict(Xte)
            out[te] = pte
            for q in qs:
                th[q][te] = np.quantile(ptr, q)
    return sl, ss, thl, ths

def oos_mask():
    return day >= MIN_TRAIN

def make_signals(sl, ss, thl, ths, mode='q', q=0.95, margin=0.0):
    """mode q: score above training quantile; mode 'abs': regression predicted pnl > margin."""
    m = valid & oos_mask() & ~np.isnan(sl)
    if mode == 'q':
        L = m & (sl > thl[q]); Sh = m & (ss > ths[q])
        el = sl - thl[q]; es = ss - ths[q]
    else:
        L = m & (sl > margin); Sh = m & (ss > margin)
        el = sl; es = ss
    sig = []
    for i in np.flatnonzero(L | Sh):
        if L[i] and Sh[i]:
            sig.append((i, 1 if el[i] >= es[i] else -1))
        elif L[i]:
            sig.append((i, 1))
        else:
            sig.append((i, -1))
    return sig

OOS_DATES = DATES[MIN_TRAIN:]

def evaluate(sig, T, S, rb=False):
    tr, st = backtest(df, sig, T, S, 'base', entry_days=OOS_DATES)
    if st.get('n', 0) == 0:
        return dict(n=0)
    _, st2 = backtest(df, sig, T, S, 'stress', entry_days=OOS_DATES)
    st['stress_total'] = st2.get('total', 0)
    if rb:
        st['p_value'] = random_baseline(df, tr, T, S, 'base', n_iter=2000, entry_days=OOS_DATES)['p_value']
    return st
