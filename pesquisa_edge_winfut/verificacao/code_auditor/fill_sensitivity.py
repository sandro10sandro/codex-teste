"""How much do pessimistic fill rules matter? Re-run time_of_day_1 (and others) under optimistic variants."""
import sys, os, glob
import numpy as np, pandas as pd
E = "/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge"
sys.path.insert(0, E + "/lib"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wf
from indep_sim import load

def sim(df, signals, target, stop, en=0, ex=0, fee=0, thr=0, tie="stop", entry_at="next_open", entry_days=None):
    o, h, l, c, T = (df[k].to_numpy(float) for k in ("open", "high", "low", "close", "tick"))
    day = df["day"].to_numpy(); tm = df["time"].to_numpy(); dt = df["date"].to_numpy(); n = len(df)
    last = {}
    for k in range(n): last[day[k]] = k
    allowed = set(entry_days); busy = -1; rows = []; ties = 0
    for i, d in sorted(set((int(i), int(d)) for i, d in signals)):
        e = i + 1
        if e >= n or day[e] != day[i] or tm[e] > 170000 or e <= busy or int(dt[e]) not in allowed: continue
        f = (o[e] if entry_at == "next_open" else c[i]) + d * en * T[e]
        tgt = f + d * (target + thr * T[e]); stp = f - d * stop
        for j in range(e, last[day[e]] + 1):
            hs = (l[j] <= stp) if d == 1 else (h[j] >= stp)
            ht = (h[j] >= tgt) if d == 1 else (l[j] <= tgt)
            if hs and ht: ties += 1
            if hs and (not ht or tie == "stop"):
                px = stp if j == e else (min(stp, o[j]) if d == 1 else max(stp, o[j])); px -= d * ex * T[j]; break
            if ht:
                px = f + d * target; break
        else:
            j = last[day[e]]; px = c[j] - d * ex * T[j]
        rows.append((dt[e], d * (px - f) - fee * T[e])); busy = j
    t = pd.DataFrame(rows, columns=["date", "pnl"])
    daily = t.groupby("date").pnl.sum().reindex(entry_days, fill_value=0.0)
    td = daily.mean() / (daily.std(ddof=1) / np.sqrt(len(daily)))
    return len(t), t.pnl.sum(), t.pnl.mean(), td, ties

days = wf.all_days()
P = {"disc": (days[:59], days[:59]), "val": (days[:79], days[59:79]), "hold": (days, days[79:]), "val+hold": (days, days[59:])}
variants = {
    "wf base (reported)": dict(en=1, ex=1, fee=.5, thr=1),
    "zero cost, touch":   dict(),
    "zero, tie->target":  dict(tie="target"),
    "zero, entry@sigclose": dict(entry_at="sig_close"),
    "base, tie->target, touch": dict(en=1, ex=1, fee=.5, thr=0, tie="target"),
}
for cand in ("time_of_day_1", "time_of_day_2"):
    m = load(f"{E}/candidates/{cand}.py")
    for per, (bd, ed) in P.items():
        df = wf.build(bd); sig = m.signals(df)
        for vn, kw in variants.items():
            n, tot, avg, td, ties = sim(df, sig, m.TARGET, m.STOP, entry_days=ed, **kw)
            print(f"{cand:14s} {per:8s} {vn:26s} n={n:3d} total={tot:8.1f} avg={avg:7.1f} t_daily={td:5.2f} same-bar-ties={ties}")
        print()
