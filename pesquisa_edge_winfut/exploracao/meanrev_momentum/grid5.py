import sys; sys.path.insert(0,'.')
from fbt import *
F=pd.read_pickle('F.pkl'); modv=F['mod'].values
rows=[]
def run(tag, s, **kw):
    for mode in ('fade','follow'):
        idx,d=sigs_from(s,mode)
        for r in evalgrid(idx,d):
            r.update(fam=tag,mode=mode,**kw); rows.append(r)
def cross(x,thr):
    xp=x.shift(1)
    return (((x>thr)&~(xp>thr)).astype(int)-((x<-thr)&~(xp<-thr)).astype(int)).values
# e) vwap by time window
for a,b in ((60,180),(180,300),(300,420)):
    for thr in (0.75,1.0,1.25):
        ev=cross(F.vwap_z,thr); s=np.where((modv>=a)&(modv<b),ev,0)
        run('vwap_win',s,a=a,thr=thr)
# g) from prior close in daily sigma units
g=df.groupby('day'); dc=g.close.last()
dsig=dc.diff().rolling(10,min_periods=5).std().shift(1)   # known before day starts
fz=F.from_pc/df.day.map(dsig).values
for thr in (1.0,1.5,2.0):
    run('from_pc',cross(fz,thr),thr=thr)
# h) runs of consecutive closes
d1=np.sign(df.close.diff().values); d1[df.first_of_day.values]=0
for k in (4,5,6,7):
    run_up=pd.Series(d1==1).groupby((pd.Series(d1!=1)).cumsum()).cumsum().values
    run_dn=pd.Series(d1==-1).groupby((pd.Series(d1!=-1)).cumsum()).cumsum().values
    s=np.where(run_up==k,1,np.where(run_dn==k,-1,0))
    run('runs',s,k=k)
# i) vol-regime conditioned
sr=(F.sig1/F.sig1.rolling(2000,min_periods=500).mean()).values
for k in (15,30):
    for thr in (2,2.5):
        ev=cross(F[f'z{k}'],thr)
        for reg,(lo,hi) in {'calm':(0,0.9),'hot':(1.15,99)}.items():
            s=np.where((sr>=lo)&(sr<hi),ev,0); run('volreg',s,k=k,thr=thr,reg=reg)
R=pd.DataFrame(rows); R.to_pickle('grid5.pkl')
print('variants',len(R))
P=R[(R.n>=40)&(R.total>0)&(R.t>=2)&(R.h1>0)&(R.h2>0)]
print('pass',len(P))
pd.set_option('display.width',250)
print(P.to_string())
print(R[R.n>=40].sort_values('t',ascending=False).head(15).to_string())
print(R.groupby(['fam','mode']).t.agg(['mean','max']).round(2))
