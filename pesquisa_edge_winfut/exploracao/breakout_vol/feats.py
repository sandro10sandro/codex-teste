from fw import *

def day_groups(df):
    starts = np.flatnonzero(df['first_of_day'].values)
    ends = np.r_[starts[1:], len(df)]
    return starts, ends

def roll_max_prev(x, day, L):
    """max of previous L bars (excluding current), within day; nan if fewer than L bars"""
    s = pd.Series(x)
    g = s.groupby(day)
    return g.transform(lambda v: v.shift(1).rolling(L, min_periods=L).max()).values

def roll_min_prev(x, day, L):
    s = pd.Series(x)
    return s.groupby(day).transform(lambda v: v.shift(1).rolling(L, min_periods=L).min()).values

def edge_events(cond_up, cond_dn, day, cooldown_reset=None):
    """emit signal at bars where cond becomes true (rising edge) within day"""
    up = cond_up & ~np.r_[False, cond_up[:-1]]
    dn = cond_dn & ~np.r_[False, cond_dn[:-1]]
    return up, dn
