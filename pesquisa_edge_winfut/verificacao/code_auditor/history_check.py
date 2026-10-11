"""Do results for a given period depend on which DataFrame (history length) they are computed on?"""
import sys, glob, os
import numpy as np, pandas as pd
E = "/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge"
sys.path.insert(0, E + "/lib"); sys.path.insert(0, os.path.dirname(__file__))
import wf
from indep_sim import load
days = wf.all_days()
D, V, H = days[:59], days[59:79], days[79:]
dfs = {"disc_only": wf.build(D), "upto_val": wf.build(days[:79]), "full": wf.build(days),
       "val_only": wf.build(V), "hold_only": wf.build(H)}
def key(df, tr):  # map to (date,time) so different frames are comparable
    return [(int(df["date"].iat[e]), int(df["time"].iat[e]), d, round(p, 3)) for e, d, p in zip(tr.entry, tr.dir, tr.pnl)]
for p in sorted(glob.glob(E + "/candidates/*.py")):
    m = load(p); name = os.path.basename(p)
    res = {}
    for fname, df in dfs.items():
        sig = m.signals(df)
        for per, ed in (("D", D), ("V", V), ("H", H)):
            if not set(ed) & set(df["date"].unique()): continue
            tr, st = wf.backtest(df, sig, m.TARGET, m.STOP, "base", entry_days=ed)
            res[(fname, per)] = (key(df, tr), st.get("total"), st.get("n"))
    for per, frames in (("D", ["disc_only", "upto_val", "full"]), ("V", ["upto_val", "full", "val_only"]), ("H", ["full", "hold_only"])):
        ref = res[(frames[0], per)]
        out = [f"{f}: n={res[(f, per)][2]} tot={res[(f, per)][1]} same={res[(f, per)][0] == ref[0]}" for f in frames]
        print(f"{name:22s} {per} | " + " | ".join(out))
