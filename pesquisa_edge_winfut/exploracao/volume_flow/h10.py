import numpy as np, pandas as pd
from es import *
import wf
df = pd.read_pickle('disc.pkl')
F = pd.read_pickle('feat4.pkl')
pd.set_option('display.width',250)
F['bret'] = F.close - F.open
nv=0; summ=[]
def run(name, sg):
    global nv
    res = bt_grid(df, sg); nv += len(res)
    r5 = res[(res['T']==500)&(res.S==500)].iloc[0]; r3 = res[(res['T']==300)&(res.S==300)].iloc[0]; r44=res[(res['T']==400)&(res.S==400)].iloc[0]
    summ.append(dict(name=name, n=r5.n, mean_tot=round(res.tot.mean()), frac_pos=round((res.tot>0).mean(),2), best_td=res.td.max(),
        td55=r5.td, tot55=r5.tot, h1_55=r5.h1, h2_55=r5.h2, td44=r44.td, td33=r3.td))
for T in (29, 30, 31, 32, 33, 34):
    S = F[(F['mod']==T)].dropna(subset=['crv'])
    sg = [(i, int(np.sign(rd)) if cr>=1 else -int(np.sign(rd))) for i,cr,rd in zip(S.index,S.crv,S.ret_day) if rd!=0]
    run(f'E1 crv-switch ret_day T={T}', sg)
S = F[(F['mod']==30)].dropna(subset=['rv_tod'])
run('E2 release-bar rv switch', [(i, int(np.sign(b)) if rv>=1 else -int(np.sign(b))) for i,rv,b in zip(S.index,S.rv_tod,S.bret) if b!=0])
S = F[(F['mod']==30)].dropna(subset=['crv'])
run('E3 follow ret_day T=30 (all days)', [(i, int(np.sign(rd))) for i,rd in zip(S.index,S.ret_day) if rd!=0])
run('E4 fade ret_day T=30 (all days)', [(i, -int(np.sign(rd))) for i,rd in zip(S.index,S.ret_day) if rd!=0])
run('E5 follow only crv>=1', [(i, int(np.sign(rd))) for i,cr,rd in zip(S.index,S.crv,S.ret_day) if rd!=0 and cr>=1])
run('E6 fade only crv<1', [(i, -int(np.sign(rd))) for i,cr,rd in zip(S.index,S.crv,S.ret_day) if rd!=0 and cr<1])
print(pd.DataFrame(summ).to_string())
print('variants', bump(nv))
