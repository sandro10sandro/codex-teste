import sys; sys.path.insert(0,'.')
from base import *
df=get_df(); F=pd.read_pickle('F.pkl')
c=df.close; day=df.day
ent=df.open.shift(-1)
def fwd(h):
    ex=c.shift(-h)
    # truncate at day end
    lastidx=df.index.to_series().groupby(day).transform('max')
    idx=np.minimum(df.index.values+h, lastidx.values)
    ex=c.values[idx]
    r=ex-ent.values
    r[df.index.values+1>lastidx.values]=np.nan
    return pd.Series(r,index=df.index)
FW={h:fwd(h) for h in (5,15,30,60)}
ok=(df.time<=165900)
half=day< (day.max()+1)//2
def clus(x,y,mask):
    m=mask & x.notna() & y.notna()
    xx=x[m]; yy=y[m]; dd=day[m]
    # slope via sign-weighted mean: mean of sign(x)*y per day
    b=np.polyfit(xx,yy,1)[0]
    # day-clustered: per-day covariance contributions
    xc=xx-xx.mean()
    num=(xc*yy).groupby(dd).sum(); den=(xc**2).sum()
    per=num/den*len(num)  # per-day slope contribution
    t=per.mean()/(per.std(ddof=1)/np.sqrt(len(per)))
    return b,t
rows=[]
for f in ['z1','z3','z5','z10','z15','z30','z60','z120','od_z','vwap_z','rpos','ma60_dev','gap_bps']:
    for h in (5,15,30,60):
        b,t=clus(F[f],FW[h],ok)
        b1,t1=clus(F[f],FW[h],ok&half); b2,t2=clus(F[f],FW[h],ok&~half)
        rows.append((f,h,round(b,1),round(t,2),round(t1,2),round(t2,2)))
print(pd.DataFrame(rows,columns=['feat','h','slope','t','t_h1','t_h2']).to_string())
