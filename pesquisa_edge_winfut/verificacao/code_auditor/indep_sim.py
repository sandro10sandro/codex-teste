"""Independent bar-by-bar re-implementation of the wf.py rules, compared trade-by-trade with wf.backtest."""
import sys, glob, os, importlib.util, json
import numpy as np, pandas as pd
E = "/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge"
sys.path.insert(0, E + "/lib")
import wf

COST = {"zero": (0, 0, 0, 0), "base": (1, 1, .5, 1), "stress": (2, 2, 1, 1)}

def sim(df, signals, target, stop, cost, entry_days=None):
    en, ex, fee, thr = COST[cost]
    o, h, l, c, T = (df[k].to_numpy(float) for k in ("open", "high", "low", "close", "tick"))
    day = df["day"].to_numpy(); tm = df["time"].to_numpy(); dt = df["date"].to_numpy()
    n = len(df)
    last = {}
    for k in range(n): last[day[k]] = k
    allowed = None if entry_days is None else set(int(x) for x in entry_days)
    busy = -1; rows = []
    for i, d in sorted(set((int(i), int(d)) for i, d in signals if d in (1, -1))):
        e = i + 1
        if e >= n or day[e] != day[i] or tm[e] > 170000 or e <= busy: continue
        if allowed is not None and int(dt[e]) not in allowed: continue
        f = o[e] + d * en * T[e]
        tgt = f + d * (target + thr * T[e]); stp = f - d * stop
        kind = 0; j_end = last[day[e]]
        for j in range(e, j_end + 1):
            hit_s = (l[j] <= stp) if d == 1 else (h[j] >= stp)
            hit_t = (h[j] >= tgt) if d == 1 else (l[j] <= tgt)
            if hit_s:
                px = stp if j == e else (min(stp, o[j]) if d == 1 else max(stp, o[j]))
                px -= d * ex * T[j]; kind = -1; break
            if hit_t:
                px = f + d * target; kind = 1; break
        else:
            j = j_end; px = c[j] - d * ex * T[j]
        rows.append((i, e, j, d, d * (px - f) - fee * T[e], kind, int(dt[e])))
        busy = j
    return pd.DataFrame(rows, columns=["signal", "entry", "exit", "dir", "pnl", "kind", "date"])

def load(p):
    spec = importlib.util.spec_from_file_location(os.path.basename(p)[:-3], p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

if __name__ == "__main__":
    days = wf.all_days()
    periods = {"discovery": (days[:59], days[:59]), "validation": (days[:79], days[59:79]), "holdout": (days, days[79:])}
    for per, (bd, ed) in periods.items():
        df = wf.build(bd)
        for p in sorted(glob.glob(E + "/candidates/*.py")):
            m = load(p); sig = m.signals(df)
            for cost in ("zero", "base", "stress"):
                tr, st = wf.backtest(df, sig, m.TARGET, m.STOP, cost, entry_days=None if per == "discovery" else ed)
                mine = sim(df, sig, m.TARGET, m.STOP, cost, None if per == "discovery" else ed)
                same = len(tr) == len(mine) and np.allclose(tr["pnl"].values, mine["pnl"].values) and \
                       (tr["entry"].values == mine["entry"].values).all() and (tr["exit"].values == mine["exit"].values).all()
                if not same or cost == "base":
                    print(f"{per:10s} {os.path.basename(p):22s} {cost:6s} wf n={st.get('n')} tot={st.get('total')}  indep n={len(mine)} tot={mine.pnl.sum():.1f}  MATCH={same}")
