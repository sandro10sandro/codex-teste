import warnings; warnings.filterwarnings('ignore')
from ev import *
df=get()
day=df.day.values; mod=df['mod'].values; cl=df.close.values
g=df.groupby('day')
dopen=g.open.transform('first').values
dclose=g.close.last()
prevc=df.day.map(dclose.shift()).values
gap=dopen-prevc
def sigB(k, mode='pullback'):
    out=[]
    for i in np.flatnonzero(mod==k):
        if np.isnan(gap[i]) or gap[i]==0: continue
        gs=np.sign(gap[i]); mv=cl[i]-dopen[i]
        if mode=='pullback' and mv*gs<0: out.append((int(i),int(gs)))
        if mode=='gapfollow': out.append((int(i),int(gs)))
        if mode=='extend' and mv*gs>0: out.append((int(i),int(gs)))
    return out
res=[]
for mode in ['pullback','gapfollow']:
  for k in [4,9,14,29]:
    R=grid(df, sigB(k,mode), show=False); R['k']=k; R['mode']=mode; res.append(R)
R=pd.concat(res)
for v in ['total','t_daily','n']:
    print(R.pivot_table(index=['mode','k'],columns='t_s',values=v).round(1).to_string())
