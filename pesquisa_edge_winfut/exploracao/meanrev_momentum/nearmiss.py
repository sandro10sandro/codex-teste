import sys; sys.path.insert(0,'.')
from fbt import *
F=pd.read_pickle('F.pkl'); modv=F['mod'].values; c=df.close.values; sig1=F.sig1.values
def cross(x,thr):
    xp=x.shift(1)
    return (((x>thr)&~(xp>thr)).astype(int)-((x<-thr)&~(xp<-thr)).astype(int)).values
cands={}
# gap fade at open
gb=F.gap_bps.values
s=np.nan_to_num(np.where(modv==0,np.sign(gb),0)).astype(int); cands['gapfade_open_400_300']=(s,'fade',400,300)
# news 9:30 fade k=3
s=np.zeros(len(df),int); ii=np.flatnonzero(modv==32); jj=ii-3; ok=df.day.values[jj]==df.day.values[ii]
s[ii[ok]]=np.sign(c[ii[ok]]-c[jj[ok]]).astype(int); cands['news930_fade_k3_400_500']=(s,'fade',400,500)
# late vwap follow 0.75
s=np.where(modv>=360,cross(F.vwap_z,0.75),0); cands['latevwap075_follow_200_400']=(s,'follow',200,400)
# open z3 fade
s=np.where(modv<40,cross(F.z3,2.0),0); cands['open_z3_fade_500_400']=(s,'fade',500,400)
for name,(s,mode,T,S) in cands.items():
    idx,d=sigs_from(s,mode)
    tr,stt=backtest(df,list(zip(idx,d)),T,S,'base')
    _,sts=backtest(df,list(zip(idx,d)),T,S,'stress')
    rb=random_baseline(df,tr,T,S,'base')
    print(name,{k:stt[k] for k in ('n','total','avg','win_rate','t_daily','first_half_total','second_half_total','profit_factor')},'stress',sts['total'],'p',rb['p_value'])
