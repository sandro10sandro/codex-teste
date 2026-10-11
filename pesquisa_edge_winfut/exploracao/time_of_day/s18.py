import warnings; warnings.filterwarnings('ignore')
from ev import *
df=get()
P=df.pivot(index='day',columns='mod',values='close').ffill(axis=1)
O=df.groupby('day').open.first()
H=df.pivot(index='day',columns='mod',values='high'); L=df.pivot(index='day',columns='mod',values='low')
print('anchor  ->h  corr  signpay  t   h1 h2  | big-move-half')
for A in [59,64,69,74,79]:
    x=P[A]-O
    for E in [89,119,149]:
        y=P[E]-P[A]
        c=np.corrcoef(x,y)[0,1]; sp=-np.sign(x)*y; t=sp.mean()/sp.std()*np.sqrt(len(sp))
        big=x.abs()>x.abs().median()
        print(A,E,round(c,2),round(sp.mean()),round(t,2),round(sp.iloc[:29].mean()),round(sp.iloc[29:].mean()),'|',round(sp[big].mean()),round(sp[~big].mean()))
# path: excursion toward open between A and 10:30 (max favorable excursion for fade)
A=69; x=P[A]-O; d=-np.sign(x)
mfe=[]; mae=[]
for dd in P.index:
    hh=H.loc[dd,A+1:89].max(); ll=L.loc[dd,A+1:89].min(); c=P.loc[dd,A]
    if d[dd]>0: mfe.append(hh-c); mae.append(c-ll)
    else: mfe.append(c-ll); mae.append(hh-c)
mfe=np.array(mfe); mae=np.array(mae)
print('fade from 10:10 until 10:30: median MFE',np.median(mfe),'median MAE',np.median(mae), 'P(MFE>400)',(mfe>400).mean(),'P(MAE>500)',(mae>500).mean())
# distance from open at 10:10 relative
print('|x| at 10:10 quantiles', x.abs().quantile([.1,.25,.5,.75,.9]).round(0).tolist())
