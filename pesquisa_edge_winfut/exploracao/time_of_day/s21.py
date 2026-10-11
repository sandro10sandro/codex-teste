import warnings; warnings.filterwarnings('ignore')
from ev import *
df=get()
day=df.day.values; mod=df['mod'].values; cl=df.close.values
dopen=df.groupby('day').open.transform('first').values
def sigS(A):
    return [(int(i),int(-np.sign(cl[i]-dopen[i]))) for i in np.flatnonzero(mod==A) if cl[i]!=dopen[i]]
rows=[]
for A in range(29,475,5):
    for ts in [(400,500),(500,500)]:
        st=wf.backtest(df,sigS(A),*ts,'base')[1]
        rows.append((A,f'{9+(A+1)//60}:{(A+1)%60:02d}',ts,st['total'],st['t_daily']))
R=pd.DataFrame(rows,columns=['A','time','ts','total','t'])
P=R.pivot_table(index=['A','time'],columns='ts',values='t')
print(P.round(1).to_string())
for ts in [(400,500),(500,500)]:
    x=R[R.ts==ts].t
    print(ts,'n slots',len(x),'mean t %.2f sd %.2f'%(x.mean(),x.std()),'n t>=2',(x>=2).sum(),'n t<=-2',(x<=-2).sum(),'n t>=3',(x>=3).sum())
bump(len(R))
