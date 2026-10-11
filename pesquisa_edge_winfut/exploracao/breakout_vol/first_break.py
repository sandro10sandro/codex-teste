from feats import *

def first_break(df, N, trig='close', mode='fade', tmax=None):
    """first time (after the N-minute opening range) price leaves the OR, either side; one signal per day."""
    mod = df['mod'].values; h = df['high'].values; l = df['low'].values; c = df['close'].values
    sigs = []
    for s, e in zip(*day_groups(df)):
        m = mod[s:e]; inor = m < N
        if inor.sum() == 0 or (~inor).sum() == 0: continue
        orh = h[s:e][inor].max(); orl = l[s:e][inor].min()
        for k in np.flatnonzero(~inor):
            i = s + k
            if tmax is not None and m[k] > tmax: break
            up = (c[i] > orh) if trig == 'close' else (h[i] > orh)
            dn = (c[i] < orl) if trig == 'close' else (l[i] < orl)
            if up and dn: break
            if up or dn:
                d = 1 if up else -1
                sigs.append((i, -d if mode == 'fade' else d))
                break
    return sigs

if __name__ == '__main__':
    df = get_df()
    res = []
    for N in (5, 10, 15, 20, 30, 45, 60):
        for trig in ('close', 'touch'):
            for mode in ('fade', 'mom'):
                sg = first_break(df, N, trig, mode)
                g = grid(df, sg); g['N'] = N; g['trig'] = trig; g['mode'] = mode
                res.append(g)
    R = pd.concat(res)
    pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
    print(R.groupby(['N','trig','mode']).agg(n=('n','mean'),tot_mean=('total','mean'),tot_min=('total','min'),tot_max=('total','max'),tmax=('t','max'),npos=('total',lambda x:(x>0).sum())))
    print(R[R.apply(passes, axis=1)].to_string())
    print('variants', VARIANTS[0])
    R.to_csv('first_break.csv', index=False)
