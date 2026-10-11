import sys; sys.path.insert(0,'.')
from base import *
df=get_df()
OUT=pickle.load(open('outcomes.pkl','rb'))
DAY=df.day.values; TM=df.time.values; N=len(df); NDAYS=int(DAY.max())+1
HALF=NDAYS//2
TSS=[(T,S) for T in (200,300,400,500) for S in (200,300,400,500)]
def fbt(idx, dirs, T, S, cost='base'):
    """idx sorted signal indices, dirs array. returns arrays of entry idx, dir, pnl"""
    pnlp,exp,_=OUT[(T,S,cost)][1]; pnlm,exm,_=OUT[(T,S,cost)][-1]
    busy=-1; E=[];D=[];P=[]
    for i,d in zip(idx,dirs):
        e=i+1
        if e>=N or DAY[e]!=DAY[i] or TM[e]>170000 or e<=busy: continue
        if d==1: p=pnlp[e]; x=exp[e]
        else: p=pnlm[e]; x=exm[e]
        E.append(e);D.append(d);P.append(p); busy=x
    return np.array(E,dtype=int),np.array(D,dtype=int),np.array(P,dtype=float)
def st(E,P):
    if len(P)==0: return dict(n=0,total=0,t=0,h1=0,h2=0)
    daily=np.bincount(DAY[E],weights=P,minlength=NDAYS)
    sd=daily.std(ddof=1)
    t=daily.mean()/(sd/np.sqrt(NDAYS)) if sd>0 else 0
    return dict(n=len(P),total=float(P.sum()),t=float(t),h1=float(daily[:HALF].sum()),h2=float(daily[HALF:].sum()),wr=float((P>0).mean()))
def sigs_from(sgn_series, mode):
    """sgn: +1/-1/0 event direction (momentum sign). mode 'fade' or 'follow'"""
    s=np.asarray(sgn_series)
    idx=np.flatnonzero(s!=0)
    d=s[idx]*(1 if mode=='follow' else -1)
    return idx,d
def evalgrid(idx,d,tss=TSS):
    res=[]
    for T,S in tss:
        E,D,P=fbt(idx,d,T,S)
        r=st(E,P); r['T']=T; r['S']=S
        res.append(r)
    return res
def full_eval(idx,d,T,S):
    E,D,P=fbt(idx,d,T,S); r=st(E,P)
    E2,D2,P2=fbt(idx,d,T,S,'stress'); r['stress']=float(P2.sum())
    return r
