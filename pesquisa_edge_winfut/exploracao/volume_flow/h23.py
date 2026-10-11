import numpy as np, pandas as pd
import sys; sys.path.insert(0,"/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/lib"); import wf
df = pd.read_pickle('disc.pkl'); F = pd.read_pickle('feat4.pkl')
S = F[(F['mod']==30)].dropna(subset=['crv'])
sg = [(i, int(np.sign(rd)) if cr>=1 else -int(np.sign(rd))) for i,cr,rd in zip(S.index,S.crv,S.ret_day) if rd!=0]
tr, st = wf.backtest(df, sg, 500, 500, 'base')
tr = tr.merge(S[['crv','ret_day']].rename_axis('signal').reset_index(), on='signal')
tr['rdt'] = tr.ret_day/df.tick.values[tr.signal]
for lab, m in (('all', tr.rdt.abs()>=0), ('|move|>=10 ticks', tr.rdt.abs()>=10), ('|move|<10', tr.rdt.abs()<10)):
    p = tr.pnl[m]; print(lab, len(p), round(p.mean(),1), 't', round(p.mean()/p.std(ddof=1)*np.sqrt(len(p)),2), 'win', round((p>0).mean(),2))
# bootstrap days
rng = np.random.default_rng(5); p = tr.pnl.values
bs = np.array([rng.choice(p, len(p)).mean() for _ in range(20000)])
print('bootstrap mean/trade 5%,50%,95%:', np.percentile(bs,[5,50,95]).round(1))
# drop best k trades
ps = np.sort(p)[::-1]
for k in (3,5,8): print('drop best', k, 'total', round(ps[k:].sum(),1))
# monthly
tr['m'] = tr.date//100; print(tr.groupby('m').pnl.agg(['size','sum','mean']).round(0))
print(tr.kind.value_counts(), 'median hold', (tr.exit-tr.entry).median())
