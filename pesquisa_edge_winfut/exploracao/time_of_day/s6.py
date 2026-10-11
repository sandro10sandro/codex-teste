import warnings; warnings.filterwarnings('ignore')
from ev import *
df=get()
day=df.day.values; mod=df['mod'].values; cl=df.close.values
dopen=df.groupby('day').open.transform('first').values
ck_cache={}
def ck(k):
    if k not in ck_cache:
        ck_cache[k]=pd.Series(np.where(mod==k, cl, np.nan)).groupby(day).transform('max').values
    return ck_cache[k]
def sig_one(k,E,sign=-1):
    c=ck(k); idx=np.flatnonzero(mod==E)
    return [(int(i), int(sign*np.sign(c[i]-dopen[i]))) for i in idx if c[i]!=dopen[i]]
res=[]
for k in [4]:
    for E in [29,59,89,119,179,239,299,359,419]:
        R=grid(df, sig_one(k,E), show=False); R['k']=k; R['E']=E; res.append(R)
R=pd.concat(res)
print(R.pivot_table(index=['k','E'],columns='t_s',values='total').round(0).to_string())
print(R.pivot_table(index=['k','E'],columns='t_s',values='t_daily').round(1).to_string())
