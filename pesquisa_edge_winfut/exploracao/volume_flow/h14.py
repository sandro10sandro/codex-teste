import numpy as np, pandas as pd
import sys; sys.path.insert(0,"/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/lib"); import wf
df = pd.read_pickle('disc.pkl'); F = pd.read_pickle('feat4.pkl')
D = {}
for T in range(26, 36):
    S = F[(F['mod']==T)].dropna(subset=['crv'])
    D[T] = pd.Series(np.where(S.crv>=1, np.sign(S.ret_day), -np.sign(S.ret_day)), index=S.day.values)
D = pd.DataFrame(D)
print('agreement with T=30 direction:', {T: round((D[T]==D[30]).mean(),2) for T in D})
# Fixed directions from T=30 but entry at different later/earlier bars: isolates timing vs direction
out = wf.outcomes(df, 400, 400, 'base')
for lag in (-3,-2,-1,0,1,2,3,5,10):
    S = F[(F['mod']==30)].dropna(subset=['crv'])
    d = np.where(S.crv>=1, np.sign(S.ret_day), -np.sign(S.ret_day)).astype(int)
    e = S.index.values + 1 + lag
    pnl = np.where(d==1, out[1][0][e], out[-1][0][e])
    print('T=30 direction, entry lag', lag, 'mean', round(np.nanmean(pnl),1), 'win', round(np.mean(pnl>0),2))
# direction from T=29 info, entry at 9:31
S29 = F[(F['mod']==29)].dropna(subset=['crv'])
d29 = np.where(S29.crv>=1, np.sign(S29.ret_day), -np.sign(S29.ret_day)).astype(int)
e = S29.index.values + 2
pnl = np.where(d29==1, out[1][0][e], out[-1][0][e]); print('T=29 direction, entry 9:31 open: mean', round(np.nanmean(pnl),1))
e = S29.index.values + 1
pnl = np.where(d29==1, out[1][0][e], out[-1][0][e]); print('T=29 direction, entry 9:30 open: mean', round(np.nanmean(pnl),1))
