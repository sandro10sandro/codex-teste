import numpy as np, pandas as pd
from es import *
F = pd.read_pickle('feat.pkl')
pd.set_option('display.width',250); pd.set_option('display.max_columns',40)
ok = ((F.time <= 165900) & (F['mod']>=5)).values
g = F.groupby('day')
# rolling relative volume over 15 bars vs tod norm: mean rv_tod over last 15 bars
F['rv15'] = F.rv_tod.groupby(F.day).transform(lambda s: s.rolling(15, min_periods=15).mean())
F['rng15'] = F.rng_tod.groupby(F.day).transform(lambda s: s.rolling(15, min_periods=15).mean())
F['ats15'] = F.ats_tod.groupby(F.day).transform(lambda s: s.rolling(15, min_periods=15).mean())
# typical 15-bar move scale: rolling median abs ret15 over prior days not needed; use ratio to rolling range
F['hi60'] = g.high.transform(lambda s: s.rolling(60, min_periods=60).max())
F['lo60'] = g.low.transform(lambda s: s.rolling(60, min_periods=60).min())
F.to_pickle('feat2.pkl')
bdir = np.nan_to_num(np.sign(F.close-F.open).values)
cdir = np.nan_to_num(np.sign(F.clv).values)
r15 = np.nan_to_num(np.sign(F.ret15).values)
rows=[]; nv=0
def add(name, ev, dirv, gap=30):
    global nv
    sg = [(i,int(dirv[i])) for i in np.flatnonzero(ev & ok & (dirv!=0))]
    sg = dedup(sg, F, gap); nv+=1
    r = fwd_study(F, sg)
    if r: rows.append(dict(name=name, **r))
q = lambda c, p: np.nanquantile(F[c].values, p)   # global quantile (research only)
# A: large trade size bars
for p in (0.9, 0.97):
    ev = F.ats_tod.values >= q('ats_tod', p)
    add(f'A ats>{p} follow bar', ev, bdir); add(f'A ats>{p} fade bar', ev, -bdir)
    add(f'A ats>{p} follow clv', ev, cdir)
    ev = F.ats15.values >= q('ats15', p)
    add(f'A ats15>{p} follow r15', ev, r15); add(f'A ats15>{p} fade r15', ev, -r15)
# B: absorption: high vol small range
for p in (0.8, 0.9):
    ev = (F.rv_tod.values >= q('rv_tod', p)) & (F.rng_tod.values <= np.nanquantile(F.rng_tod, 0.5))
    add(f'B absorb{p} fade r15', ev, -r15); add(f'B absorb{p} follow clv', ev, cdir)
    ev = (F.rv15.values >= q('rv15', p)) & (F.rng15.values <= np.nanquantile(F.rng15, 0.5))
    add(f'B absorb15_{p} fade r15', ev, -r15); add(f'B absorb15_{p} follow r15', ev, r15)
# C: new 60-bar high/low with low vs high volume
nh = F.high.values >= F.hi60.values; nl = F.low.values <= F.lo60.values
brk = np.where(nh, 1, np.where(nl, -1, 0))
for lab, cond in (('lowvol', F.rv15.values <= np.nanquantile(F.rv15, 0.3)), ('hivol', F.rv15.values >= np.nanquantile(F.rv15, 0.7))):
    add(f'C brk60 {lab} follow', cond, brk); add(f'C brk60 {lab} fade', cond, -brk)
# D: big move on low volume -> fade
big = np.abs(F.ret15.values) >= np.nanquantile(np.abs(F.ret15.values), 0.8)
add('D bigmove lowvol fade', big & (F.rv15.values <= np.nanquantile(F.rv15, 0.4)), -r15)
add('D bigmove hivol follow', big & (F.rv15.values >= np.nanquantile(F.rv15, 0.6)), r15)
add('D bigmove hivol fade', big & (F.rv15.values >= np.nanquantile(F.rv15, 0.6)), -r15)
# E: price-pressure divergence
for N in (15, 30, 60):
    rr = F[f'ret{N}'].values; pp = F[f'press{N}'].values
    ev = np.abs(rr) >= np.nanquantile(np.abs(rr), 0.6)
    dv = (np.sign(rr) != np.sign(pp))
    add(f'E div{N} follow press', ev & dv, np.nan_to_num(np.sign(pp)))
    add(f'E conf{N} fade', ev & ~dv, -np.nan_to_num(np.sign(rr)))
out = pd.DataFrame(rows)
print(out[['name','n','fwd15','fwd30','fwd30_t','fwd60','fwd60_t','L500_500','L500_500_t','L500_500_h1','L500_500_h2','L300_300','L300_300_t']].to_string())
print('variants', bump(nv))
