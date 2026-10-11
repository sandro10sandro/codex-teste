import warnings; warnings.filterwarnings('ignore')
from ev import *
df=get()
day=df.day.values; mod=df['mod'].values; cl=df.close.values
g=df.groupby('day')
dopen=g.open.transform('first').values
prevc=df.day.map(g.close.last().shift()).values
gap=dopen-prevc
def sigF(k):
    return [(int(i), int(-np.sign(gap[i]))) for i in np.flatnonzero(mod==k) if not np.isnan(gap[i]) and gap[i]!=0]
res=[]
for k in [0,2,4]:
    R=grid(df, sigF(k), show=False); R['k']=k; res.append(R)
R=pd.concat(res)
for v in ['total','t_daily']:
    print(R.pivot_table(index=['k'],columns='t_s',values=v).round(1).to_string())
# gap magnitude: how much of gap fills in first 15 min
G=pd.DataFrame({'gap':gap,'day':day,'mod':mod,'cl':cl,'o':dopen})
d=G[G['mod']==14].dropna()
d['fill']=-(d.cl-d.o)/d.gap
print(d.fill.describe())
