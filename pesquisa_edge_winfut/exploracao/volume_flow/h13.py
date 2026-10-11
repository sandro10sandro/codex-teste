import numpy as np, pandas as pd
import sys; sys.path.insert(0,"/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/lib"); import wf
df = pd.read_pickle('disc.pkl'); F = pd.read_pickle('feat4.pkl')
pd.set_option('display.width',250); pd.set_option('display.max_rows',100)
S = F[(F['mod']==30)].dropna(subset=['crv'])
sg = [(i, int(np.sign(rd)) if cr>=1 else -int(np.sign(rd))) for i,cr,rd in zip(S.index,S.crv,S.ret_day) if rd!=0]
tr, st = wf.backtest(df, sg, 400, 400, 'base')
tr = tr.merge(S[['crv','ret_day','dow','rv_tod']].rename_axis('signal').reset_index(), on='signal')
tr['rd_ticks'] = (tr.ret_day / df.tick.values[tr.signal]).round(0)
tr['hold'] = tr.exit - tr.entry
print(tr[['date','dow','crv','rv_tod','rd_ticks','dir','pnl','kind','hold']].round(2).to_string())
print(st)
print(tr.groupby('dow').pnl.agg(['count','sum','mean']).round(0))
print(tr.groupby(tr.crv>=1).pnl.agg(['count','sum','mean']).round(0))
print('abs ret_day small (<10 ticks):', tr[tr.rd_ticks.abs()<10].pnl.agg(['count','sum','mean']).round(0).to_dict())
print('abs ret_day big   (>=10 ticks):', tr[tr.rd_ticks.abs()>=10].pnl.agg(['count','sum','mean']).round(0).to_dict())
