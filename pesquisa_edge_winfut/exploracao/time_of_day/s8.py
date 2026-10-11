import warnings; warnings.filterwarnings('ignore')
from ev import *
df=get()
P=df.pivot(index='day',columns='mod',values='close').ffill(axis=1)
O=df.groupby('day').open.first(); C=df.groupby('day').close.last()
P[-1]=O  # open as "close of bar -1"
rows=[]
for w in [30,60]:
    for a in range(0,480,30):
        if a+2*w>510: continue
        x=P[a+w-1]-P[a-1]; y=P[min(a+2*w-1,509)]-P[a+w-1]
        c=np.corrcoef(x,y)[0,1]; sp=np.sign(x)*y; t=sp.mean()/sp.std()*np.sqrt(len(sp))
        rows.append((w,f'{9+a//60:02d}:{a%60:02d}',round(c,2),round(t,2), round(sp.iloc[:29].mean()), round(sp.iloc[29:].mean())))
gap=(O-C.shift()).iloc[1:]
for k in [0,4,14,29,59]:
    y=(P[k]-O).iloc[1:]
    c=np.corrcoef(gap,y)[0,1]; sp=np.sign(gap)*y; t=sp.mean()/sp.std()*np.sqrt(len(sp))
    rows.append(('gap',f'f{k+1}',round(c,2),round(t,2),round(sp.iloc[:29].mean()),round(sp.iloc[29:].mean())))
# prev day last 30/60 -> today first 30/60/day
for lw in [30,60]:
    xl=(C-P[509-lw]).shift().iloc[1:]
    for k in [29,59,509]:
        y=(P[k]-O).iloc[1:]
        c=np.corrcoef(xl,y)[0,1]; sp=np.sign(xl)*y; t=sp.mean()/sp.std()*np.sqrt(len(sp))
        rows.append((f'prevlast{lw}',f'f{k+1}',round(c,2),round(t,2),round(sp.iloc[:29].mean()),round(sp.iloc[29:].mean())))
    y=(O-C.shift()).iloc[1:]
    c=np.corrcoef(xl,y)[0,1]; sp=np.sign(xl)*y; t=sp.mean()/sp.std()*np.sqrt(len(sp))
    rows.append((f'prevlast{lw}','gap',round(c,2),round(t,2),round(sp.iloc[:29].mean()),round(sp.iloc[29:].mean())))
R=pd.DataFrame(rows,columns=['w','start','corr','t','h1','h2'])
print(R.to_string())
bump(len(R))
