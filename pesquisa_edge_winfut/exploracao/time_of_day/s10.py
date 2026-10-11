import warnings; warnings.filterwarnings('ignore')
from ev import *
df=get()
P=df.pivot(index='day',columns='mod',values='close').ffill(axis=1)
O=df.groupby('day').open.first()
H=df.pivot(index='day',columns='mod',values='high'); L=df.pivot(index='day',columns='mod',values='low')
x=P[29]-O; y1=P[59]-P[29]; y2=P[89]-P[29]; yc=P[509]-P[29]
rg30=H.loc[:,0:29].max(axis=1)-L.loc[:,0:29].min(axis=1)
pos=(P[29]-L.loc[:,0:29].min(axis=1))/rg30   # close location in first 30 min range
D=pd.DataFrame({'x':x,'y1':y1,'y2':y2,'yc':yc,'rg':rg30,'pos':pos})
D['q']=pd.qcut(D.x,5,labels=False)
print(D.groupby('q')[['x','y1','y2','yc']].mean().round(0))
D['qp']=pd.qcut(D.pos,5,labels=False)
print(D.groupby('qp')[['pos','x','y1','y2','yc']].mean().round(2))
print(np.corrcoef(D.pos,D.y1)[0,1], np.corrcoef(D.pos,D.y2)[0,1])
