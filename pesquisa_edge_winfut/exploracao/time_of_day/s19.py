import warnings; warnings.filterwarnings('ignore')
from ev import *
df=get()
day=df.day.values; mod=df['mod'].values; cl=df.close.values
dopen=df.groupby('day').open.transform('first').values
def sigS(A):
    return [(int(i),int(-np.sign(cl[i]-dopen[i]))) for i in np.flatnonzero(mod==A) if cl[i]!=dopen[i]]
res=[]
for A in [61,64,67,69,71,74,77,80,84]:
    R=grid(df, sigS(A), show=False); R['A']=A; res.append(R)
R=pd.concat(res)
for v in ['total','t_daily']:
    print(R.pivot_table(index=['A'],columns='t_s',values=v).round(1).to_string())
