import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/lib')
from wf import load
import numpy as np, pandas as pd
df = load()
df.to_pickle('disc.pkl')
print(df.shape, df.date.min(), df.date.max(), df.day.nunique())
print(df.head(3).T)
print(df[['trades','qty','vol','tick']].describe())
print(df.groupby('day').size().value_counts())
# time-of-day profile of qty
prof = df.groupby(df['mod']//30)[['trades','qty']].median()
print(prof)
# daily range in pts
rng = df.groupby('day').agg(h=('high','max'), l=('low','min'), c=('close','last'))
print(((rng.h-rng.l)).describe())
print((df.high-df.low).describe())
print(df.groupby('day').real_close.last().describe())
