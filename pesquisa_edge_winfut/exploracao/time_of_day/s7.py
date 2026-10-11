import warnings; warnings.filterwarnings('ignore')
from ev import *
df=get()
b=df['mod'].values//30
ok=(df.time.values<=170000)
rows=[]
for t,s in [(500,500),(300,300),(500,300),(300,500)]:
    out=wf.outcomes(df,t,s,'base')
    for d in (1,-1):
        p=out[d][0]
        x=pd.DataFrame({'p':p,'b':b,'day':df.day.values,'dow':df.dow.values})[ok]
        # day-clustered mean per bucket
        g=x.groupby(['b','day']).p.mean().groupby('b')
        m=g.mean(); se=g.std()/np.sqrt(g.count())
        rows.append(pd.DataFrame({'ts':f'{t}/{s}','d':d,'mean':m.round(0),'t':(m/se).round(1)}))
R=pd.concat(rows)
print(R.reset_index().pivot_table(index='b',columns=['ts','d'],values=['mean']).round(0).to_string())
print(R.reset_index().pivot_table(index='b',columns=['ts','d'],values=['t']).round(1).to_string())
# DOW
out=wf.outcomes(df,500,500,'base')
for d in (1,-1):
    x=pd.DataFrame({'p':out[d][0],'day':df.day.values,'dow':df.dow.values})[ok]
    g=x.groupby(['dow','day']).p.mean().groupby('dow')
    print('dir',d,'DOW mean', g.mean().round(0).to_dict(), 't',(g.mean()/(g.std()/np.sqrt(g.count()))).round(1).to_dict(), 'ndays',g.count().to_dict())
D=df.groupby('day').agg(o=('open','first'),c=('close','last'),dow=('dow','first'))
D['r']=D.c-D.o
print(D.groupby('dow').r.agg(['mean','std','count']).round(0))
