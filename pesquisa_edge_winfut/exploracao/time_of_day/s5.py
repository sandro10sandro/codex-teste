import warnings; warnings.filterwarnings('ignore')
from ev import *
df=get()
P=df.pivot(index='day',columns='mod',values='close').ffill(axis=1)
for m,hz in [(3,30),(1,30),(5,30),(3,15)]:
    out=[]
    for T in range(1,480):
        x=P[T+m-1]-P[T-1]; y=P[min(T+m-1+hz,509)]-P[T+m-1]
        out.append((T,np.corrcoef(x,y)[0,1]))
    C=pd.Series(dict(out))
    print(m,hz,'mean corr all minutes %.3f sd %.3f'%(C.mean(),C.std()), ' T30 %.2f T120 %.2f'%(C[30],C[120]), 'rank T30', (C<C[30]).sum(), 'rank T120',(C<C[120]).sum(), 'of',len(C))
    # by 30-min bucket
    print((C.groupby(C.index//30).mean()).round(2).to_dict())
