import sys; sys.path.insert(0,'.')
from fbt import *
F=pd.read_pickle(sys.argv[1] if len(sys.argv)>1 else 'F.pkl')
def cross(x,thr):
    xp=x.shift(1)
    return ((x>thr)&~(xp>thr)).astype(int)-((x<-thr)&~(xp<-thr)).astype(int)
fam=[]
for k in (1,3,5,10,15,30,60,120):
    for thr in (2,2.5,3,3.5): fam.append((f'z{k}',thr))
for thr in (1.5,2,2.5,3): fam.append(('ma60_dev',thr))
for thr in (0.5,0.75,1,1.25,1.5): fam.append(('vwap_z',thr))
for thr in (1,1.5,2,2.5,3): fam.append(('od_z',thr))
rows=[]
for f,thr in fam:
    s=cross(F[f],thr)
    for mode in ('fade','follow'):
        idx,d=sigs_from(s,mode)
        for r in evalgrid(idx,d):
            r.update(f=f,thr=thr,mode=mode); rows.append(r)
R=pd.DataFrame(rows)
R.to_pickle(sys.argv[2] if len(sys.argv)>2 else 'grid1.pkl')
print('variants',len(R))
P=R[(R.n>=40)&(R.total>0)&(R.t>=2)&(R.h1>0)&(R.h2>0)]
print('pass(pre-stress)',len(P))
pd.set_option('display.width',200)
print(P.sort_values('t',ascending=False).head(40).to_string())
print(R.groupby(['f','mode']).t.mean().unstack().round(2))
