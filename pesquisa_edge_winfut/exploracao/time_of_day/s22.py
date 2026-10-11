import warnings; warnings.filterwarnings('ignore')
from ev import *
df=get()
day=df.day.values; mod=df['mod'].values; cl=df.close.values
dopen=df.groupby('day').open.transform('first').values
def sigS(A,sign=1):
    return [(int(i),int(sign*np.sign(cl[i]-dopen[i]))) for i in np.flatnonzero(mod==A) if cl[i]!=dopen[i]]
def sigW(S,E,sign=1):
    return [(int(i),int(sign*np.sign(cl[i]-dopen[i]))) for i in np.flatnonzero((mod>=S)&(mod<E)) if cl[i]!=dopen[i]]
res=[]
for A in [179,184,189,194,199,204]:
    R=grid(df, sigS(A), show=False); R['A']=A; res.append(R)
for (S,E) in [(180,210),(185,205)]:
    R=grid(df, sigW(S,E), show=False); R['A']=f'W{S}-{E}'; res.append(R)
R=pd.concat(res); R['A']=R.A.astype(str)
for v in ['total','t_daily','first_half_total','second_half_total']:
    print(v); print(R.pivot_table(index=['A'],columns='t_s',values=v).round(1).to_string())
