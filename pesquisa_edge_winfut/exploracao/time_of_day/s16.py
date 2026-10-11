import warnings; warnings.filterwarnings('ignore')
from ev import *
df=get()
day=df.day.values; mod=df['mod'].values; cl=df.close.values
dopen=df.groupby('day').open.transform('first').values
def sigO(S,E):
    out=[]
    for i in np.flatnonzero((mod>=S)&(mod<E)):
        d=np.sign(cl[i]-dopen[i])
        if d!=0: out.append((int(i),int(-d)))
    return out
res=[]
for (S,E) in [(60,90),(55,90),(65,90),(70,90),(60,85),(60,95),(60,100),(65,95)]:
    R=grid(df, sigO(S,E), show=False); R['W']=f'{S}-{E}'; res.append(R)
R=pd.concat(res)
for v in ['total','t_daily']:
    print(R.pivot_table(index=['W'],columns='t_s',values=v).round(1).to_string())
R.to_pickle('s16.pkl')
