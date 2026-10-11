import sys; sys.path.insert(0,'.')
from fbt import *
F=pd.read_pickle('F.pkl')
modv=F['mod'].values; c=df.close.values
rows=[]
def run(tag, s, **kw):
    for mode in ('fade','follow'):
        idx,d=sigs_from(s,mode)
        for r in evalgrid(idx,d):
            r.update(fam=tag,mode=mode,**kw); rows.append(r)
# b) prior day return at 9:00 bar close
g=df.groupby('day')
dret=(g.close.last()-g.open.first())/g.open.first()*1e4
pdr=df.day.map(dret.shift(1)).values
for thr in (0,50):
    s=np.where((modv==0)&(np.abs(pdr)>thr),np.sign(pdr),0)
    s=np.nan_to_num(s).astype(int)
    run('prevday',s,thr=thr)
# c) first-hour trend
odz=F.od_z.values; od=F.od.values
for m in (59,89):
    for thr in (0,0.5,1.0):
        s=np.where((modv==m)&(np.abs(odz)>thr),np.sign(od),0).astype(int)
        run('fh_single',s,m=m,thr=thr)
        # repeated: every bar after m whose od_z sign agrees with the sign at m and |od_z|>thr
        sm=pd.Series(np.where(modv==m,np.sign(od)*(np.abs(odz)>thr),np.nan)).groupby(df.day.values).ffill().values
        s2=np.where((modv>=m)&(~np.isnan(sm))&(sm!=0)&(np.sign(od)==sm)&(np.abs(odz)>thr),sm,0)
        s2=np.nan_to_num(s2).astype(int)
        run('fh_repeat',s2,m=m,thr=thr)
# d) late-day
for m in (390,420,450):
    for f in ('od','from_pc','vwap_dev'):
        v=F[f].values
        s=np.where(modv==m,np.sign(v),0); s=np.nan_to_num(s).astype(int)
        run('late',s,m=m,f=f)
# e) late vwap fade
for thr in (0.75,1.0,1.25):
    x=F.vwap_z; xp=x.shift(1)
    ev=(((x>thr)&~(xp>thr)).astype(int)-((x<-thr)&~(xp<-thr)).astype(int)).values
    s=np.where(modv>=360,ev,0)
    run('latevwap',s,thr=thr)
R=pd.DataFrame(rows); R.to_pickle('grid4.pkl')
print('variants',len(R))
P=R[(R.n>=40)&(R.total>0)&(R.t>=2)&(R.h1>0)&(R.h2>0)]
print('pass',len(P))
pd.set_option('display.width',250)
print(P.to_string())
print(R[R.n>=40].sort_values('t',ascending=False).head(20).to_string())
print(R.groupby(['fam','mode']).t.agg(['mean','max']).round(2))
