from levels_lib import *
df = get()
c = df['close'].values; mod = df['mod'].values; day = df['day'].values
s = pd.Series(c)
for N in (30, 60):
    hi = s.groupby(day).transform(lambda x: x.shift(1).rolling(N, min_periods=N).max()).values
    lo = s.groupby(day).transform(lambda x: x.shift(1).rolling(N, min_periods=N).min()).values
    sig = []
    lastu = lastd = -999
    for i in range(len(df)):
        if np.isnan(hi[i]): continue
        if c[i] > hi[i]:
            if i - lastu > N: sig.append((i, 1))
            lastu = i
        if c[i] < lo[i]:
            if i - lastd > N: sig.append((i, -1))
            lastd = i
    evaluate(df, f'generic first new {N}-bar close extreme', sig)
print('variants so far', total_count())
