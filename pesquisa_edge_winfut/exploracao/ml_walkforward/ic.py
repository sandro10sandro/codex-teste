from sym import *
from scipy.stats import spearmanr
def oos_ic(sl, ss, T, S):
    yl, ys = labels(T, S)
    m = valid & ~np.isnan(sl)
    x = np.r_[sl[m], ss[m]]; y = np.r_[yl[m], ys[m]]; d = np.r_[day[m], day[m]]
    ic = [spearmanr(x[d == k], y[d == k]).correlation for k in np.unique(d)]
    ic = np.array(ic)
    # decile mean pnl
    qs = pd.qcut(pd.Series(x).rank(method='first'), 10, labels=False)
    dec = pd.Series(y).groupby(qs.values).mean().round(1).tolist()
    return round(np.nanmean(ic), 4), round(np.nanmean(ic) / (np.nanstd(ic) / np.sqrt(len(ic))), 2), dec
