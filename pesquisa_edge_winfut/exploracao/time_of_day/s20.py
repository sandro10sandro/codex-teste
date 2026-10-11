import warnings; warnings.filterwarnings('ignore')
from ev import *
df=get()
P=df.pivot(index='day',columns='mod',values='close').ffill(axis=1)
O=df.groupby('day').open.first(); C=df.groupby('day').close.last()
PC=C.shift()
print('anchor comparison, signal 10:10 (mod69) -> 10:30 (mod89) and -> 11:00')
for name,anc in [('prevclose',PC),('open0900',O),('0915',P[14]),('0930',P[29]),('0945',P[44]),('1000',P[59])]:
    x=P[69]-anc; ok=x.notna()
    for E in [89,119]:
        y=P[E]-P[69]; sp=(-np.sign(x)*y)[ok]; t=sp.mean()/sp.std()*np.sqrt(len(sp))
        print(f'{name:10s} ->{E} mean {sp.mean():6.0f} t {t:5.2f}')
print('fade since open, 20-min horizon, by time of day')
rows=[]
for T in range(29,480,30):
    x=P[T+10]-O; y=P[T+30]-P[T+10]; sp=-np.sign(x)*y
    rows.append((f'{9+(T+11)//60}:{(T+11)%60:02d}', round(sp.mean()), round(sp.mean()/sp.std()*np.sqrt(59),2)))
print(pd.DataFrame(rows,columns=['sig_time','mean','t']).to_string(index=False))
