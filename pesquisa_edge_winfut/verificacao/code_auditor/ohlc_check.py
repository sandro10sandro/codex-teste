import sys, numpy as np
sys.path.insert(0, "/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/lib")
import wf
df = wf.build(wf.all_days())
o,h,l,c,t = (df[k].values for k in ("open","high","low","close","tick"))
print("low<=min(o,c):", (l <= np.minimum(o,c)+1e-6).mean(), " high>=max(o,c):", (h >= np.maximum(o,c)-1e-6).mean())
same = df["day"].values[1:] == df["day"].values[:-1]
print("mean |open[i+1]-close[i]| (ticks):", np.mean(np.abs(o[1:]-c[:-1])[same]/t[1:][same]))
print("mean |close[i+1]-open[i+1]| (ticks):", np.mean(np.abs(c[1:]-o[1:])[same]/t[1:][same]))
print("mean |open[i+1]-open[i]| (ticks):", np.mean(np.abs(o[1:]-o[:-1])[same]/t[1:][same]))
print("frac open[i+1]==close[i]:", np.mean(np.abs(o[1:]-c[:-1])[same] < 1e-3))
