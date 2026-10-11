import sys; sys.path.insert(0,'.')
from fbt import *
F=pd.read_pickle('F.pkl')
modv=F['mod'].values
rows=[]
def run(tag, s, **kw):
    for mode in ('fade','follow'):
        idx,d=sigs_from(s,mode)
        for r in evalgrid(idx,d):
            r.update(fam=tag,mode=mode,**kw); rows.append(r)
# F11 pullback in trend: trend sign from ctx, pullback against trend on zk -> event sign = trend sign (follow = with trend)
for ctx in ('od_z','vwap_z'):
    for t1 in (0.5,1.0,1.5):
        for k in (5,15):
            for t2 in (1.0,1.5,2.0):
                c=F[ctx].values; z=F[f'z{k}'].values
                tr=np.where(c>t1,1,np.where(c<-t1,-1,0))
                pb=(tr!=0)&(z*tr< -t2)
                pbp=np.r_[False,pb[:-1]]
                ev=pb&~pbp
                s=np.where(ev,tr,0)
                run('pullback',s,ctx=ctx,t1=t1,k=k,t2=t2)
# F6 gap at time m
for m in (0,14,29):
    for thr in (0,20,40,60):
        gb=F.gap_bps.values
        s=np.where((modv==m)&(np.abs(gb)>thr),np.sign(gb),0)
        run('gap',s,m=m,thr=thr)
# VWAP cross after 10:00
for thr in (0,0.25,0.5):
    vz=F.vwap_z.values
    above=vz>thr; below=vz<-thr
    # event: becomes above having been below -thr more recently than above (simple: sign state change)
    state=np.where(above,1,np.where(below,-1,0)).astype(float)
    st_=pd.Series(state).replace(0,np.nan).groupby(df.day.values).ffill().fillna(0).values
    prev=np.r_[0,st_[:-1]]
    newday=df.first_of_day.values
    ev=(st_!=prev)&(st_!=0)&(prev!=0)&~newday&(modv>=60)
    s=np.where(ev,st_,0).astype(int)
    run('vwapx',s,thr=thr)
R=pd.DataFrame(rows); R.to_pickle('grid2.pkl')
print('variants',len(R))
P=R[(R.n>=40)&(R.total>0)&(R.t>=2)&(R.h1>0)&(R.h2>0)]
print('pass',len(P))
pd.set_option('display.width',250)
print(R[R.n>=40].sort_values('t',ascending=False).head(30).to_string())
print(R.groupby(['fam','mode']).t.agg(['mean','max']).round(2))
