import numpy as np, pandas as pd
from es import *
F = pd.read_pickle('feat.pkl')
ok = ((F.time <= 165900) & (F['mod']>=3)).values
pd.set_option('display.width',250); pd.set_option('display.max_columns',40)
rows=[]; nv=0
bdir = np.sign(F.close-F.open).values
for k in (2.5, 3, 4, 5):
  for mv in ('bar','ret5','ret15'):
    if mv=='bar': dirv = bdir
    else: dirv = np.sign(F[mv].values)
    ev = ok & (F.rv_tod.values>=k) & (np.nan_to_num(dirv)!=0)
    for mode in ('fade','follow'):
        sg = [(i, int(-dirv[i] if mode=='fade' else dirv[i])) for i in np.flatnonzero(ev)]
        sg = dedup(sg, F, 30)
        r = fwd_study(F, sg); nv+=1
        if r: rows.append(dict(k=k,mv=mv,mode=mode,**r))
print(pd.DataFrame(rows)[['k','mv','mode','n','fwd15','fwd30','fwd30_t','fwd60','fwd60_t','L500_500','L500_500_t','L500_500_h1','L500_500_h2','L300_300','L300_300_t']])
print('variants', bump(nv))
