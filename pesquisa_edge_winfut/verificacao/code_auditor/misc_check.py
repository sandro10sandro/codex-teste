import sys, os
import numpy as np, pandas as pd
E = "/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge"
sys.path.insert(0, E + "/lib"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wf
from indep_sim import load
days = wf.all_days(); df = wf.build(days)
# missing minutes
for d in (20120809, 20120815, 20120528, 20120704, 20120903):
    g = df[df.date == d]; allm = set(range(510)); miss = sorted(allm - set(g["mod"]))
    print(d, "missing mods:", miss)
m = load(f"{E}/candidates/time_of_day_1.py"); sig = m.signals(df)
H = days[79:]
tr, st = wf.backtest(df, sig, 500, 500, "base", entry_days=H)
daily = tr.groupby("date").pnl.sum().reindex(H, fill_value=0.0)
for lab, dd in (("20 days", daily), ("19 days (drop 35-bar 2012-09-20)", daily.iloc[:-1])):
    print(lab, "t_daily=%.3f" % (dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd)))))
# per-trade and day-clustered SE, CI, and test of discovery effect size
se_day = daily.std(ddof=1) * np.sqrt(len(daily)) / len(tr)
avg = tr.pnl.mean()
print(f"holdout avg/trade={avg:.1f}  day-clustered SE/trade={se_day:.1f}  95% CI=[{avg-1.96*se_day:.0f},{avg+1.96*se_day:.0f}]")
print(f"z vs discovery avg 125.4: {(avg-125.4)/se_day:.2f}")
# target exits where the bar opened beyond target (limit would have filled better)
out = wf.outcomes(df, 500, 500, "base")
o = df.open.values; T = df.tick.values
gaps = 0
for e, d, x, k in zip(tr.entry, tr.dir, tr.exit, tr.kind):
    if k == 1:
        f = o[e] + d * T[e]; tgt = f + d * 500
        if x > e and d * (o[x] - tgt) > 0: gaps += 1
print("holdout target exits with favorable gap at exit-bar open:", gaps, "of", (tr.kind == 1).sum())
# power: probability the pre-registered holdout test passes if true per-trade edge = delta.
# resample holdout days (day bootstrap of trade lists), shift each trade's pnl by (delta - observed avg)
rb = wf.random_baseline(df, tr, 500, 500, "base", n_iter=5000, entry_days=H)
crit = rb["random_p95"]
rng = np.random.default_rng(5)
groups = [g.pnl.values for _, g in tr.groupby("date")] + [np.array([])] * (len(H) - tr.date.nunique())
for delta in (0, 30, 60, 90, 125):
    passes = 0
    for _ in range(4000):
        pick = rng.integers(len(groups), size=len(H))
        p = np.concatenate([groups[k] for k in pick]) - avg + delta
        stress_ok = (p - 24).sum() > 0  # stress costs ~ 2 extra ticks/trade approx
        passes += (p.sum() > crit) and stress_ok and len(p) >= 15
    print(f"true edge {delta:4d} pts/trade -> P(pass holdout as pre-registered) ~ {passes/4000:.2f}")
