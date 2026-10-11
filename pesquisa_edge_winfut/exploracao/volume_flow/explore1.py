import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/lib')
from wf import outcomes
import numpy as np, pandas as pd
from feat import add_features
df = pd.read_pickle('disc.pkl')
F = add_features(df)
# forward returns from entry at open of i+1
g = F.groupby('day')
o_next = g.open.shift(-1)
for H in (5, 15, 30, 60):
    F[f'fwd{H}'] = g.close.shift(-H).values - o_next.values
for t,s in [(500,500),(300,300),(200,200)]:
    out = outcomes(df, t, s, 'zero')
    # pnl of entering at open of i+1 => shift by -1
    F[f'L{t}_{s}'] = pd.Series(out[1][0]).shift(-1).values
    F[f'S{t}_{s}'] = pd.Series(out[-1][0]).shift(-1).values
F.to_pickle('feat.pkl')
ok = (F.time <= 165900) & F['fwd30'].notna()
print('unconditional means (zero cost):')
print(F.loc[ok, ['fwd5','fwd15','fwd30','fwd60','L500_500','S500_500','L300_300','S300_300']].mean())
print(F.loc[ok].groupby(F['mod']//60)[['fwd30','L500_500','S500_500']].mean())
