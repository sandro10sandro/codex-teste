import sys, numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/lib")
import wf
raw = wf._raw()
print(raw["aft"].value_counts())
print("dup (date,time):", raw.duplicated(["date","time"]).sum())
print("unsorted:", (np.diff(raw["date"].values*1000000+raw["time"].values) <= 0).sum())
days = wf.all_days()
print(len(days), days[0], days[58], days[59], days[78], days[79], days[-1])
df = wf.build(days)
g = df.groupby("date")
s = pd.DataFrame(dict(nbars=g.size(), first=g["time"].first(), last=g["time"].last(), tick=g["tick"].first(),
                      maxgap=g["mod"].apply(lambda m: np.diff(m.values).max() if len(m)>1 else 0)))
s["seg"] = ["D" if i<59 else ("V" if i<79 else "H") for i in range(len(s))]
pd.set_option("display.max_rows", 200, "display.width", 200)
print(s.to_string())
# check ticks: are all prices on a grid of tick per day?
bad = []
for d, gg in df.groupby("date"):
    px = np.unique(np.concatenate([gg[c].values for c in ("open","high","low","close")]))
    t = gg["tick"].iloc[0]
    r = (px - px.min())/t
    dev = np.abs(r - np.round(r)).max()
    diffs = np.diff(px)
    bad.append((d, t, dev, diffs.min(), np.median(diffs), np.round(diffs/t,3)[:0]))
b = pd.DataFrame(bad, columns=["date","tick","maxdev_ticks","mindiff","meddiff","x"])
print(b.drop(columns="x").describe())
print(b.sort_values("maxdev_ticks").tail(5))
