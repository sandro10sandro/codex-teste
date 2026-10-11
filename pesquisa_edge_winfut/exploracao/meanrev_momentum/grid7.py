import sys; sys.path.insert(0,'.')
from fbt import *
F=pd.read_pickle('F.pkl'); modv=F['mod'].values
rows=[]
gs=np.sign(F.gap.values); fp=np.sign(F.from_pc.values)
for N in (15,30,60):
    s=np.where((modv<N)&(gs!=0)&(fp==gs),gs,0); s=np.nan_to_num(s).astype(int)
    for mode in ('fade','follow'):
        idx,d=sigs_from(s,mode)
        for r in evalgrid(idx,d):
            r.update(fam='gap_reentry',N=N,mode=mode); rows.append(r)
R=pd.DataFrame(rows); R.to_pickle('grid7.pkl')
print('variants',len(R))
pd.set_option('display.width',250)
for k,g in R.groupby(['N','mode']):
    print(k,'n',g.n.min(),g.n.max()); print(g.pivot(index='T',columns='S',values='t').round(2))
P=R[(R.n>=40)&(R.total>0)&(R.t>=2)&(R.h1>0)&(R.h2>0)]
print(P)
