from feats import *
df = get_df()

def failed_orb(df, N, trig='close', maxwait=None):
    """after first break of OR (by close or touch), signal when close returns inside OR -> fade."""
    mod = df['mod'].values; h = df['high'].values; l = df['low'].values; c = df['close'].values
    sigs = []
    for s, e in zip(*day_groups(df)):
        m = mod[s:e]; inor = m < N
        if inor.sum() == 0 or (~inor).sum() == 0: continue
        orh = h[s:e][inor].max(); orl = l[s:e][inor].min()
        bu = bd = None; du = dd = False
        for k in np.flatnonzero(~inor):
            i = s + k
            if bu is None and ((c[i] > orh) if trig == 'close' else (h[i] > orh)):
                bu = i
            elif bu is not None and not du and c[i] < orh and i > bu:
                if maxwait is None or i - bu <= maxwait:
                    sigs.append((i, -1))
                du = True
            if bd is None and ((c[i] < orl) if trig == 'close' else (l[i] < orl)):
                bd = i
            elif bd is not None and not dd and c[i] > orl and i > bd:
                if maxwait is None or i - bd <= maxwait:
                    sigs.append((i, 1))
                dd = True
    return sigs

res = []
for N in (15, 30, 60):
    for trig in ('close', 'touch'):
        for mw in (None, 15):
            sg = failed_orb(df, N, trig, mw)
            g = grid(df, sg); g['N'] = N; g['trig'] = trig; g['mw'] = str(mw)
            res.append(g)
R = pd.concat(res)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
print(R.groupby(['N','trig','mw']).agg(n=('n','mean'),tot_mean=('total','mean'),tot_max=('total','max'),tmax=('t','max'),npos=('total',lambda x:(x>0).sum())))
print(R[R.apply(passes, axis=1)])
print('variants', VARIANTS[0])
R.to_csv('failed.csv', index=False)
