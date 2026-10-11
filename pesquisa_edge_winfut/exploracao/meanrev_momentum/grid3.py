import sys; sys.path.insert(0,'.')
from fbt import *
F=pd.read_pickle('F.pkl')
modv=F['mod'].values; c=df.close.values; sig1=F.sig1.values
rows=[]
def run(tag, s, **kw):
    for mode in ('fade','follow'):
        idx,d=sigs_from(s,mode)
        for r in evalgrid(idx,d):
            r.update(fam=tag,mode=mode,**kw); rows.append(r)
# news reaction
for evs in ((30,),(90,),(120,),(30,90,120)):
    for k in (1,3,5,10):
        for thr in (0,0.5):
            s=np.zeros(len(df),int)
            for ev in evs:
                # bar index where mod==ev+k-1 ; return from close of bar mod==ev-1
                m=modv==ev+k-1
                ii=np.flatnonzero(m)
                jj=ii-k
                ok=(df.day.values[jj]==df.day.values[ii])
                ii=ii[ok]; jj=jj[ok]
                r=c[ii]-c[jj]; z=r/(sig1[ii]*np.sqrt(k))
                sel=np.abs(z)>thr
                s[ii[sel]]=np.sign(r[sel]).astype(int)
            run('news',s,evs=str(evs),k=k,thr=thr)
# volume-conditioned big moves
q=df.qty.astype(float)
for k in (5,15,30):
    qk=q.groupby(df.day).transform(lambda x: x.rolling(k,min_periods=k).sum())
    piv=pd.DataFrame({'day':df.day,'mod':df['mod'],'qk':qk}).pivot(index='day',columns='mod',values='qk')
    exp_=piv.shift(1).rolling(10,min_periods=3).mean()
    ratio=(piv/exp_).stack().reindex(pd.MultiIndex.from_arrays([df.day,df['mod']])).values
    for thr in (2,2.5):
        x=F[f'z{k}']; xp=x.shift(1)
        ev=(((x>thr)&~(xp>thr)).astype(int)-((x<-thr)&~(xp<-thr)).astype(int)).values
        for cls,(lo,hi) in {'high':(1.5,1e9),'low':(0,1.0)}.items():
            s=np.where((ratio>=lo)&(ratio<hi),ev,0)
            run('volcond',s,k=k,thr=thr,cls=cls)
R=pd.DataFrame(rows); R.to_pickle('grid3.pkl')
print('variants',len(R))
P=R[(R.n>=40)&(R.total>0)&(R.t>=2)&(R.h1>0)&(R.h2>0)]
print('pass',len(P))
pd.set_option('display.width',250)
print(P.to_string())
print(R[R.n>=40].sort_values('t',ascending=False).head(25).to_string())
print(R.groupby(['fam','mode']).t.agg(['mean','max']).round(2))
