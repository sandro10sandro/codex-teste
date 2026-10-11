"""Selection-aware null for the release-minute volume switch family.
Family searched: T in {10,15,20,25,30,35,40,45,60,90} x 16 target/stop, one trade/day.
Null A: shuffle the hi/lo volume label across days (direction source kept).
Null B: random direction per day."""
import numpy as np, pandas as pd
import sys; sys.path.insert(0,"/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/lib"); import wf
df = pd.read_pickle('disc.pkl')
F = pd.read_pickle('feat4.pkl')
Ts = (10,15,20,25,30,35,40,45,60,90)
combos = [(t,s) for t in wf.TARGETS for s in wf.STOPS]
outs = {c: wf.outcomes(df, c[0], c[1], 'base') for c in combos}
days = sorted(F.day.unique())
# per T: entry index per day, ret_day sign, crv label
info = {}
for T in Ts:
    S = F[(F['mod']==T)].dropna(subset=['crv'])
    S = S[S.ret_day!=0]
    info[T] = (S.index.values+1, np.sign(S.ret_day.values).astype(int), (S.crv.values>=1), S.day.values)
def tday(pnl, dd):
    s = pd.Series(pnl).groupby(dd).sum().reindex(days, fill_value=0.0).values
    return s.mean()/(s.std(ddof=1)/np.sqrt(len(s)))
def maxt(labels_by_day=None, dirs_by_day=None):
    best=-9
    for T in Ts:
        e, rd, hi, dd = info[T]
        if labels_by_day is not None: hi = labels_by_day[dd]
        d = np.where(hi, rd, -rd) if dirs_by_day is None else dirs_by_day[dd]
        for c in combos:
            pl = np.where(d==1, outs[c][1][0][e], outs[c][-1][0][e])
            best = max(best, tday(pl, dd))
    return best
obs = maxt()
print('observed max t over family', round(obs,2))
rng = np.random.default_rng(11)
nd = int(F.day.max())+1
hi_frac = np.mean(info[30][2])
nullA=[]; nullB=[]
for k in range(300):
    lab = rng.random(nd) < hi_frac
    nullA.append(maxt(labels_by_day=lab))
    nullB.append(maxt(dirs_by_day=np.where(rng.random(nd)<0.5,1,-1)))
nullA=np.array(nullA); nullB=np.array(nullB)
print('NullA (shuffle vol label): mean max t', nullA.mean().round(2), 'p95', np.percentile(nullA,95).round(2), 'p(>=obs)', (nullA>=obs).mean())
print('NullB (random dir/day):   mean max t', nullB.mean().round(2), 'p95', np.percentile(nullB,95).round(2), 'p(>=obs)', (nullB>=obs).mean())
