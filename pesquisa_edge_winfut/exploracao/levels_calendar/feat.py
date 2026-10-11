from common import *

def features(df):
    f = pd.DataFrame(index=df.index)
    day = df['day'].values
    g = df.groupby('day')
    dh = g['high'].max(); dl = g['low'].min(); dc = g['close'].last(); do = g['open'].first()
    f['pdh'] = df['day'].map(dh.shift(1)); f['pdl'] = df['day'].map(dl.shift(1))
    f['pdc'] = df['day'].map(dc.shift(1)); f['pdo'] = df['day'].map(do.shift(1))
    f['dopen'] = df['day'].map(do)
    f['hod'] = g['high'].cummax(); f['lod'] = g['low'].cummin()
    f['hod_prev'] = f.groupby(day)['hod'].shift(1); f['lod_prev'] = f.groupby(day)['lod'].shift(1)
    f['prev_close'] = g['close'].shift(1)
    return f
