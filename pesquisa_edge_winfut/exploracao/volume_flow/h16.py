import numpy as np, pandas as pd
import sys; sys.path.insert(0,"/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/lib"); import wf
df = pd.read_pickle('disc.pkl'); F = pd.read_pickle('feat4.pkl')
S = F[(F['mod']==30)].dropna(subset=['crv'])
sg = [(i, int(np.sign(rd)) if cr>=1 else -int(np.sign(rd))) for i,cr,rd in zip(S.index,S.crv,S.ret_day) if rd!=0]
for t,s in [(400,400),(500,500),(300,400),(500,400)]:
    tr, st = wf.backtest(df, sg, t, s, 'base'); trs, sts = wf.backtest(df, sg, t, s, 'stress')
    rb = wf.random_baseline(df, tr, t, s, 'base')
    print(t,s, 'n',st['n'],'tot',st['total'],'td',st['t_daily'],'h1',st['first_half_total'],'h2',st['second_half_total'],'stress',sts['total'],'p',rb)
