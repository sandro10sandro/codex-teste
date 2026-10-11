import sys; sys.path.insert(0,'.')
from fbt import *
F=pd.read_pickle('F.pkl'); modv=F['mod'].values
rows=[]
for start in (300,330,360,390,420):
    for thr in (0.5,0.6,0.7,0.75,0.8,0.9,1.0):
        x=F.vwap_z; xp=x.shift(1)
        ev=(((x>thr)&~(xp>thr)).astype(int)-((x<-thr)&~(xp<-thr)).astype(int)).values
        s=np.where(modv>=start,ev,0)
        idx,d=sigs_from(s,'follow')
        for T,S in ((200,400),(300,300),(300,400),(500,500)):
            E,D,P=fbt(idx,d,T,S); r=st(E,P); r.update(start=start,thr=thr,T=T,S=S); rows.append(r)
R=pd.DataFrame(rows)
print(len(R))
print(R.pivot_table(index=['start','thr'],columns=['T','S'],values='t').round(2))
print(R.pivot_table(index=['start','thr'],columns=['T','S'],values='n').iloc[:, :1].T)
