"""Is wf.random_baseline anti-conservative because same-day trades are correlated? Compare with clustered nulls."""
import sys, os
import numpy as np, pandas as pd
E = "/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge"
sys.path.insert(0, E + "/lib"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wf
from indep_sim import load
days = wf.all_days()
P = {"discovery": (days[:59], days[:59]), "validation": (days[:79], days[59:79]), "holdout": (days, days[79:])}
NIT = 5000
for cand in ("time_of_day_1", "time_of_day_2", "levels_calendar_2"):
    m = load(f"{E}/candidates/{cand}.py")
    for per, (bd, ed) in P.items():
        df = wf.build(bd); sig = m.signals(df)
        tr, st = wf.backtest(df, sig, m.TARGET, m.STOP, "base", entry_days=ed)
        rb = wf.random_baseline(df, tr, m.TARGET, m.STOP, "base", n_iter=NIT, entry_days=ed)
        out = wf.outcomes(df, m.TARGET, m.STOP, "base")
        rng = np.random.default_rng(11)
        actual = tr.pnl.sum()
        # (1) day-shuffle null: move each strategy-day's whole set of (minute, dir) entries onto a random eval day
        dfe = df[df["date"].isin(ed)]
        key = {(int(d), int(mm)): int(ix) for ix, d, mm in zip(dfe.index, dfe["date"], dfe["mod"])}
        mods = df["mod"].values
        groups = [(g["entry"].map(lambda e: mods[e]).values, g["dir"].values) for _, g in tr.groupby("date")]
        sims = np.zeros(NIT)
        for k in range(NIT):
            s = 0.0
            for mm, dd in groups:
                d0 = ed[rng.integers(len(ed))]
                for a, b in zip(mm, dd):
                    ix = key.get((d0, int(a)))
                    if ix is None:   # missing minute (short/partial day): draw another day
                        cands = [x for x in ed if (x, int(a)) in key]; ix = key[(cands[rng.integers(len(cands))], int(a))]
                    s += out[int(b)][0][ix]
            sims[k] = s
        p_dayshuf = (sims >= actual).mean()
        # (2) random direction per day (sign flip by day), same entry bars; pnl of opposite direction from same bar
        alt = np.array([out[-int(d)][0][e] for e, d in zip(tr.entry, tr.dir)])
        own = tr.pnl.values; dates = tr.date.values; ud = np.unique(dates)
        flips = rng.integers(0, 2, size=(NIT, len(ud))).astype(bool)
        dix = np.searchsorted(ud, dates)
        sims2 = np.where(flips[:, dix], alt[None, :], own[None, :]).sum(1)
        p_flip = (sims2 >= actual).mean()
        # (3) one-sided p from daily t (normal approx) and day bootstrap of daily pnl
        daily = tr.groupby("date").pnl.sum().reindex(ed, fill_value=0.0).values
        bs = rng.choice(daily, size=(NIT, len(daily))).mean(1)
        p_boot = (bs <= 0).mean()
        # intraday correlation of trade pnls
        tr2 = tr.copy(); tr2["dm"] = tr2.groupby("date").pnl.transform("mean")
        var_iid = len(tr) * tr.pnl.var(); var_day = len(ed) * daily.var()
        print(f"{cand:18s} {per:10s} n={st['n']:3d} total={actual:8.1f} t_daily={st['t_daily']}  "
              f"p_random_baseline={rb['p_value']:.4f}  p_dayshuffle={p_dayshuf:.4f}  p_dayflip={p_flip:.4f}  "
              f"p_dayboot(total<=0)={p_boot:.4f}  var(daily-sum)/var(iid-sum)={var_day/var_iid:.2f}  "
              f"sd null rb={np.std(np.zeros(1))} ")
