import warnings; warnings.filterwarnings('ignore')
from ev import *
df=get()
day=df.day.values; mod=df['mod'].values; cl=df.close.values
dopen=df.groupby('day').open.transform('first').values
def sigM(L,S,E,sign=-1):
    out=[]
    for i in np.flatnonzero((mod>=S)&(mod<E)&(mod>=L)):
        j=i-L
        if day[j]!=day[i]: continue
        d=np.sign(cl[i]-cl[j])
        if d!=0: out.append((int(i),int(sign*d)))
    return out
# single trade at 10:00 fading 09:00-10:00 move
s1=[(int(i),int(-np.sign(cl[i]-dopen[i]))) for i in np.flatnonzero(mod==59) if cl[i]!=dopen[i]]
R=grid(df,s1,label='single 10:00 fade first hour')
# details best cells of M rule
for L,ts in [(60,(400,500)),(60,(500,500)),(60,(500,300)),(45,(400,500)),(75,(400,500)),(90,(400,500))]:
    sig=sigM(L,60,90)
    r=ev(df,sig,*ts,rb=True); print(L,ts,r)
bump(3)
