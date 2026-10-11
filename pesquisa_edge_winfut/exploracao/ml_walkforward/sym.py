"""Direction-symmetric pooled model: one model for 'trade in direction d wins', using features aligned with d."""
from wfml import *

SIGNED = ['r1','r3','r5','r10','r15','r30','r60','r120','r_day','gap','d_prevclose','prev_day_ret','d_vwap',
          'z5','z15','z30','z60','z_vwap','z_day','sflow5','sflow15','sflow60','updown15','updown60','clv1']
PAIRS = [('d_high', 'd_low'), ('d_prevhigh', 'd_prevlow')]   # under flip: d_high -> -d_low
UNSIGNED = ['mod','mod2','open_bucket','close_bucket','vol15','vol60','brng15','brng60','vol_ratio','q_ratio5_60',
            'q_ratio15_60','q_vs_tod','avg_trade_size','eff15','eff60','range_so_far','prev_range']
POS = ['pos_in_range']

def aligned(cols, d):
    out = {}
    for c in cols:
        x = F[c].values
        if c in SIGNED:
            out[c] = d * x
        elif c in UNSIGNED:
            out[c] = x
        elif c == 'pos_in_range':
            out[c] = x if d == 1 else 1 - x
        elif c in ('d_high', 'd_low', 'd_prevhigh', 'd_prevlow'):
            if d == 1:
                out[c] = x
            else:
                partner = {'d_high': 'd_low', 'd_low': 'd_high', 'd_prevhigh': 'd_prevlow', 'd_prevlow': 'd_prevhigh'}[c]
                out[c] = -F[partner].values
        else:
            raise KeyError(c)
    return np.column_stack([out[c] for c in cols])

def wf_sym(cols, T, S, kind, sub=1, qs=(0.80, 0.90, 0.95, 0.98), min_train=MIN_TRAIN, step=STEP, **kw):
    yl, ys = labels(T, S)
    XL = aligned(cols, 1); XS = aligned(cols, -1)
    sl = np.full(n, np.nan); ss = np.full(n, np.nan)
    th = {q: np.full(n, np.nan) for q in qs}
    typ, mk = make_model(kind, **kw)
    models = []
    for start in range(min_train, len(DATES), step):
        idx = np.flatnonzero(valid & (day < start))[::sub]
        te = (day >= start) & (day < start + step)
        Xtr = np.vstack([XL[idx], XS[idx]]); ytr = np.r_[yl[idx], ys[idx]]
        sc = StandardScaler().fit(Xtr)
        m = mk()
        if typ == 'clf':
            m.fit(sc.transform(Xtr), (ytr > 0).astype(int))
            f = lambda X: m.predict_proba(sc.transform(X))[:, 1]
        else:
            m.fit(sc.transform(Xtr), ytr)
            f = lambda X: m.predict(sc.transform(X))
        ptr = f(Xtr)
        sl[te] = f(XL[te]); ss[te] = f(XS[te])
        for q in qs:
            th[q][te] = np.quantile(ptr, q)
        models.append((start, m, sc))
    return sl, ss, th, th, models
