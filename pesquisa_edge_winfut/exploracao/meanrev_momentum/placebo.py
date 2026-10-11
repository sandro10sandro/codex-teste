import sys; sys.path.insert(0,'.')
from fbt import *
F=pd.read_pickle('F.pkl')
def cross(x,thr):
    xp=x.shift(1)
    return (((x>thr)&~(xp>thr)).astype(int)-((x<-thr)&~(xp<-thr)).astype(int)).values
fam=[]
for k in (1,3,5,10,15,30,60,120):
    for thr in (2,2.5,3,3.5): fam.append((f'z{k}',thr))
for thr in (1.5,2,2.5,3): fam.append(('ma60_dev',thr))
for thr in (0.5,0.75,1,1.25,1.5): fam.append(('vwap_z',thr))
for thr in (1,1.5,2,2.5,3): fam.append(('od_z',thr))
out=[]
for seed in range(6):
    rng=np.random.default_rng(100+seed)
    flip=rng.choice([-1,1],size=len(df))
    npass=0; ts=[]
    for f,thr in fam:
        s=cross(F[f],thr)*flip
        idx,d=sigs_from(s,'follow')
        for r in evalgrid(idx,d):
            ts.append(r['t'] if r['n']>=40 else np.nan)
            if r['n']>=40 and r['total']>0 and r['t']>=2 and r['h1']>0 and r['h2']>0: npass+=1
    ts=np.array(ts)
    out.append((seed,npass,np.nanmax(ts),np.nanmean(ts)))
    print(seed,npass,round(np.nanmax(ts),2),round(np.nanmean(ts),2),flush=True)
