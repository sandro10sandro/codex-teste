import sys; sys.path.insert(0,'.')
from fbt import *
F=pd.read_pickle('F.pkl'); modv=F['mod'].values
def cross(x,thr):
    xp=x.shift(1)
    return (((x>thr)&~(xp>thr)).astype(int)-((x<-thr)&~(xp<-thr)).astype(int)).values
fam=[]
for k in (1,5,15,30,60):
    for thr in (2,2.5,3): fam.append((f'z{k}',thr))
for thr in (0.75,1,1.25): fam.append(('vwap_z',thr))
for thr in (1.5,2,2.5): fam.append(('od_z',thr))
rows=[]
for f,thr in fam:
    s=cross(F[f],thr)
    for mode in ('fade','follow'):
        idx,d=sigs_from(s,mode)
        for side in (1,-1):
            m=d==side
            for r in evalgrid(idx[m],d[m]):
                r.update(fam='side',f=f,thr=thr,mode=mode,side=side); rows.append(r)
# opening-window z fade/follow (first 40 minutes)
for k in (3,5,10):
    for thr in (1.5,2,2.5):
        s=np.where(modv<40,cross(F[f'z{k}'],thr),0)
        for mode in ('fade','follow'):
            idx,d=sigs_from(s,mode)
            for r in evalgrid(idx,d):
                r.update(fam='open_z',f=f'z{k}',thr=thr,mode=mode); rows.append(r)
R=pd.DataFrame(rows); R.to_pickle('grid6.pkl')
print('variants',len(R))
P=R[(R.n>=40)&(R.total>0)&(R.t>=2)&(R.h1>0)&(R.h2>0)]
print('pass',len(P))
pd.set_option('display.width',250)
print(P.to_string())
print(R[R.n>=40].sort_values('t',ascending=False).head(15).to_string())
print(R.groupby(['fam','mode','side'],dropna=False).t.agg(['mean','max']).round(2))
