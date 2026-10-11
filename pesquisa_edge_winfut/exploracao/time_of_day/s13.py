import warnings; warnings.filterwarnings('ignore')
from ev import *
df=get()
day=df.day.values; mod=df['mod'].values; cl=df.close.values
def sigM(L,S,E,sign=-1):
    out=[]
    for i in np.flatnonzero((mod>=S)&(mod<E)&(mod>=L)):
        j=i-L
        if day[j]!=day[i]: continue
        d=np.sign(cl[i]-cl[j])
        if d!=0: out.append((int(i),int(sign*d)))
    return out
res=[]
for L in [15,30,60]:
    for (S,E) in [(30,120),(60,120),(60,90)]:
        R=grid(df, sigM(L,S,E), show=False); R['L']=L; R['W']=f'{S}-{E}'; res.append(R)
R=pd.concat(res)
for v in ['total','t_daily','n']:
    print(R.pivot_table(index=['L','W'],columns='t_s',values=v).round(1).to_string())
R.to_pickle('s13.pkl')
