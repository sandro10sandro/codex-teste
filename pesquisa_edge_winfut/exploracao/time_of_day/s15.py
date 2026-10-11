import warnings; warnings.filterwarnings('ignore')
from ev import *
df=get()
day=df.day.values; mod=df['mod'].values
def table(t,s,Ls,Ts,step=5):
    out=wf.outcomes(df,t,s,'base')
    P=df.pivot(index='day',columns='mod',values='close').ffill(axis=1)
    R=pd.DataFrame(index=P.index,columns=range(510),dtype=float)
    rowidx=df.pivot(index='day',columns='mod',values='mod')*0
    ri=pd.DataFrame(np.full(P.shape,-1),index=P.index,columns=P.columns)
    for d,m,k in zip(day,mod,range(len(df))): ri.at[d,m]=k
    res={}; tst={}
    for L in Ls:
        col=[];ct=[]
        for T in Ts:
            A=[]
            for T2 in range(T,T+step):
                if T2-L<0 or T2+1>509: continue
                x=(P[T2]-P[T2-L]).values; e=ri[T2+1].values
                v=np.full(len(x),np.nan)
                for q in range(len(x)):
                    if x[q]!=0 and e[q]>=0:
                        dd=int(-np.sign(x[q])); v[q]=out[dd][0][e[q]]
                A.append(v)
            if not A: col.append(np.nan); ct.append(np.nan); continue
            A=np.nanmean(np.array(A),axis=0)
            col.append(np.nanmean(A)); ct.append(np.nanmean(A)/np.nanstd(A)*np.sqrt(np.isfinite(A).sum()))
        res[L]=col; tst[L]=ct
    lab=[f'{9+T//60}:{T%60:02d}' for T in Ts]
    return pd.DataFrame(res,index=lab), pd.DataFrame(tst,index=lab)
if __name__=='__main__':
    m,t=table(400,500,[15,30,45,60,75,90],range(30,150,5))
    print(pd.concat([m.round(0),t.round(1)],axis=1,keys=['mean','t']).to_string())
