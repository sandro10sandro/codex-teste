from ev import *
df=get()
P=df.pivot(index='day',columns='mod',values='close').ffill(axis=1)
Op=df.pivot(index='day',columns='mod',values='open')
H=df.pivot(index='day',columns='mod',values='high'); L=df.pivot(index='day',columns='mod',values='low')
rows=[]
for T in [30,60,90,120,240,330]:   # 09:30,10:00,10:30,11:00,13:00,14:30
    for m in [1,2,3,5]:
        x = P[T+m-1]-P[T-1]                      # move in event window
        base = (H.loc[:,T-30:T-1].max(1)-L.loc[:,T-30:T-1].min(1))   # range previous 30 min
        z = x/base
        for hz in [5,15,30]:
            y = P[T+m-1+hz]-P[T+m-1]
            c = np.corrcoef(x,y)[0,1]
            sp = np.sign(x)*y; t=sp.mean()/sp.std()*np.sqrt(len(sp))
            big = z.abs()>z.abs().median()
            sb = sp[big]; tb = sb.mean()/sb.std()*np.sqrt(len(sb))
            rows.append((T,m,hz,round(c,2),round(sp.mean()),round(t,2),round(sb.mean()),round(tb,2)))
R=pd.DataFrame(rows,columns=['T','m','hz','corr','signpay','t','pay_big','t_big'])
print(R.to_string())
bump(len(R)*2)
