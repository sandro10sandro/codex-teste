from common import *
def px_at(df, mod):
    """close of bar with mod == mod (per day) -> Series by day"""
    s = df[df['mod']==mod].set_index('day')['close']
    return s
def daily(df):
    g = df.groupby('day')
    D = pd.DataFrame({'open': g.open.first(), 'close': g.close.last(), 'hi': g.high.max(), 'lo': g.low.min(), 'dow': g.dow.first()})
    for m in [0,4,14,29,59,89,119,179,239,299,359,389,419,449,479,509]:
        D[f'c{m}'] = px_at(df, m)
    D['prev_close'] = D.close.shift()
    return D
