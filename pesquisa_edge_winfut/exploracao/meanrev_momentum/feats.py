import sys; sys.path.insert(0,'.')
from base import *

def features(df):
    c=df.close.values.astype(float); o=df.open.values.astype(float); h=df.high.values.astype(float); l=df.low.values.astype(float)
    day=df.day.values; n=len(df)
    F=pd.DataFrame(index=df.index)
    s_c=pd.Series(c, index=df.index)
    first=df.first_of_day.values
    d1=s_c.diff(); d1[first]=np.nan
    sig1=d1.rolling(120,min_periods=30).std()
    F['sig1']=sig1
    F['mod']=df['mod'].values
    for k in (1,3,5,10,15,30,60,120):
        r=s_c-s_c.shift(k)
        same=pd.Series(day,index=df.index).shift(k).values==day
        r[~same]=np.nan
        F[f'r{k}']=r
        F[f'z{k}']=r/(sig1*np.sqrt(k))
    g=df.groupby('day')
    dopen=g.open.transform('first')
    F['od']=s_c-dopen
    F['od_z']=F.od/(sig1*np.sqrt(df['mod']+1))
    tp=(df.high+df.low+df.close)/3
    q=df.qty.astype(float)
    cumpq=(tp*q).groupby(df.day).cumsum(); cumq=q.groupby(df.day).cumsum()
    vwap=cumpq/cumq
    F['vwap_dev']=s_c-vwap
    F['vwap_z']=F.vwap_dev/(sig1*np.sqrt(df['mod']+1))
    F['vwap_bps']=F.vwap_dev/s_c*1e4
    hs=g.high.cummax(); ls=g.low.cummin()
    F['rpos']=(s_c-ls)/(hs-ls).replace(0,np.nan)
    F['dhi']=s_c-hs; F['dlo']=s_c-ls
    # prev day close / gap
    lastc=df.close.where(df.last_of_day)
    prevc=lastc.shift(1).ffill()
    prevc_day=pd.Series(np.where(first, prevc, np.nan), index=df.index).groupby(df.day).transform('first')
    # prevc at first bar: last close of previous day
    pc=df.close.shift(1).where(df.first_of_day)
    pc=pc.groupby(df.day).transform('first')
    F['gap']=dopen-pc
    F['gap_bps']=F.gap/pc*1e4
    F['from_pc']=s_c-pc
    # previous day range/return
    dret=(g.close.transform('last')-dopen)
    F['ma60_dev']=(s_c-s_c.rolling(60,min_periods=30).mean())/(sig1*np.sqrt(30))
    F['vol_rel']=q/q.rolling(120,min_periods=30).mean()
    return F

if __name__=='__main__':
    df=get_df(); F=features(df); F.to_pickle('F.pkl'); print(F.describe().T.to_string())
