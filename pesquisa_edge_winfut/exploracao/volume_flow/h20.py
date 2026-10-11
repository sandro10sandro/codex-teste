import numpy as np, pandas as pd
import sys; sys.path.insert(0,"/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/lib"); import wf
from es import bump
df = pd.read_pickle('disc.pkl'); F = pd.read_pickle('feat4.pkl')
out = wf.outcomes(df, 400, 400, 'zero')
S = F[(F['mod']==30)].dropna(subset=['crv']).copy()
e = S.index.values+1
S['bdir'] = np.sign(S.close-S.open); S['rdir']=np.sign(S.ret_day)
S['pre_dir'] = np.sign(S.open - F.open.values[S.index.values-30])   # move 9:00->9:30 open (pre-release)
S['fol_bar'] = np.where(S.bdir==1, out[1][0][e], out[-1][0][e])
S['fol_pre'] = np.where(S.pre_dir==1, out[1][0][e], out[-1][0][e])
S['hi'] = S.crv>=1
S['rvhi'] = S.rv_tod>=1
S['h'] = (S.day>=29).astype(int)
print('follow release bar overall', S.fol_bar.mean().round(1), ' follow pre-release move overall', S.fol_pre.mean().round(1))
print(S.groupby(['hi']).agg(n=('fol_pre','size'), fol_pre=('fol_pre','mean'), fol_bar=('fol_bar','mean')).round(1))
print(S.groupby(['rvhi']).agg(n=('fol_pre','size'), fol_pre=('fol_pre','mean'), fol_bar=('fol_bar','mean')).round(1))
print('agreement bar vs pre', (S.bdir==S.pre_dir).mean().round(2), ' ret_day vs pre', (S.rdir==S.pre_dir).mean().round(2))
print(S.groupby(['hi','h']).fol_pre.agg(['size','mean']).round(1))
bump(6)
