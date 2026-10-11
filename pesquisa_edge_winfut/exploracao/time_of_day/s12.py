import warnings; warnings.filterwarnings('ignore')
from ev import *
df=get()
P=df.pivot(index='day',columns='mod',values='close').ffill(axis=1).values
nd,nm=P.shape
res={}
for L in [15,30,60]:
    for Hh in [15,30,60]:
        rows=[]
        for b in range(17):
            pays=[]
            for T in range(b*30, b*30+30):
                if T-L<0 or T+Hh>509: continue
                x=P[:,T]-P[:,T-L]; y=P[:,T+Hh]-P[:,T]
                pays.append(np.sign(x)*y)
            if not pays: rows.append(np.nan); continue
            pay=np.mean(pays,axis=0)   # per-day average over minutes in bucket
            rows.append(pay.mean()/pay.std()*np.sqrt(nd))
        res[(L,Hh)]=rows
R=pd.DataFrame(res,index=[f'{9+b//2:02d}:{(b%2)*30:02d}' for b in range(17)])
print(R.round(1).to_string())
bump(153)
