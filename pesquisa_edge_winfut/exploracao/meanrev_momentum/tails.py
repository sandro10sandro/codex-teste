import sys; sys.path.insert(0,'.')
from base import *
exec(open('fwd.py').read().split('rows=[]')[0])
def events(x, thr, mask):
    # crossing above thr (positive events) and below -thr (negative)
    xp=x.shift(1)
    up=(x>thr)&~(xp>thr)&mask
    dn=(x<-thr)&~(xp<-thr)&mask
    sgn=pd.Series(0,index=x.index); sgn[up]=1; sgn[dn]=-1
    # can't cross on first bar of day if xp from previous day: allow
    return sgn
rows=[]
for f,thrs in [('z1',[2,3,4]),('z5',[2,2.5,3]),('z15',[2,2.5,3]),('z30',[2,2.5,3]),('z60',[1.5,2,2.5]),('z120',[1.5,2,2.5]),('od_z',[1.5,2,2.5,3]),('vwap_z',[0.75,1,1.25,1.5]),('ma60_dev',[1.5,2,2.5,3])]:
    for thr in thrs:
        s=events(F[f],thr,ok)
        m=s!=0
        for h in (5,15,30,60):
            y=(FW[h]*s)[m].dropna()   # momentum-signed return
            dd=day[y.index]
            per=y.groupby(dd).sum()
            per=per.reindex(range(59),fill_value=0)
            t=per.mean()/(per.std()/np.sqrt(59))
            h1=y[dd<29].sum(); h2=y[dd>=29].sum()
            rows.append((f,thr,h,len(y),round(y.mean(),1),round(t,2),round(h1),round(h2)))
pd.set_option('display.width',200)
print(pd.DataFrame(rows,columns=['feat','thr','h','n','mom_mean','t','h1','h2']).to_string())
