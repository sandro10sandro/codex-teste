from feats import *

def window_break(df, a, b, trig='close', mode='fade', tmax=None):
    """range = bars with a <= mod < b; first break after b (either side) -> fade. one per day"""
    mod = df['mod'].values; h = df['high'].values; l = df['low'].values; c = df['close'].values
    sigs = []
    for s, e in zip(*day_groups(df)):
        m = mod[s:e]; inr = (m >= a) & (m < b)
        if inr.sum() == 0: continue
        rh = h[s:e][inr].max(); rl = l[s:e][inr].min()
        for k in np.flatnonzero(m >= b):
            i = s + k
            if tmax is not None and m[k] > tmax: break
            up = (c[i] > rh) if trig == 'close' else (h[i] > rh)
            dn = (c[i] < rl) if trig == 'close' else (l[i] < rl)
            if up and dn: break
            if up or dn:
                d = 1 if up else -1
                sigs.append((i, -d if mode == 'fade' else d)); break
    return sigs

if __name__ == '__main__':
    df = get_df()
    res = []
    for a, b in [(0, 25), (0, 35), (0, 40), (60, 75), (60, 90), (90, 120), (120, 150), (180, 210), (300, 330)]:
        sg = window_break(df, a, b)
        g = grid(df, sg); g['a'] = a; g['b'] = b; res.append(g)
    R = pd.concat(res)
    pd.set_option('display.width', 250)
    print(R.groupby(['a', 'b']).agg(n=('n','mean'),tot_mean=('total','mean'),tot_min=('total','min'),tot_max=('total','max'),tmax=('t','max'),tmin=('t','min'),npos=('total',lambda x:(x>0).sum())))
    print('variants', VARIANTS[0])
