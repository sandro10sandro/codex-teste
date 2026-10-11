from ev import *
from feats import *
df=get()
P=df.pivot(index='day',columns='mod',values='close')
O=df.groupby('day').open.first()
P=P.ffill(axis=1)
rows=[]
for k in [0,2,4,9,14,29]:
    x=np.sign(P[k]-O)
    for E in [29,59,89,119,179,239,299,359]:
        if E<=k: continue
        for H in ['close',60]:
            end = P[509] if H=='close' else P[min(E+60,509)]
            y=(end-P[E])*(-x)
            t=y.mean()/y.std()*np.sqrt(len(y))
            h1=y.iloc[:29].mean(); h2=y.iloc[29:].mean()
            rows.append((k,E,H,round(y.mean()),round(t,2),round(h1),round(h2)))
R=pd.DataFrame(rows,columns=['k','E','H','mean','t','h1','h2'])
print(R.pivot_table(index=['k'],columns=['H','E'],values='t').round(1).to_string())
bump(len(R))
