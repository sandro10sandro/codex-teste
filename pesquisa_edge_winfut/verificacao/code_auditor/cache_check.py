"""Can wf.outcomes() return a stale cached result for a different DataFrame? And does evaluate.py ever hit it?"""
import sys, gc
import numpy as np
E = "/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge"
sys.path.insert(0, E + "/lib")
import wf
base = wf.load()
# 1) in-place mutation of the SAME object (same id, len, first/last close) -> stale
a = base.copy()
r1 = wf.outcomes(a, 500, 500, "base")[1][0].copy()
a["high"] = a["high"] + 1000.0          # every long should now hit target much more often
r2 = wf.outcomes(a, 500, 500, "base")[1][0]
print("in-place mutation returns stale cache:", np.allclose(r1, r2, equal_nan=True))
# 2) id reuse after garbage collection
hits = 0
for k in range(200):
    x = base.copy(); xid = id(x)
    wf.outcomes(x, 500, 500, "base"); del x; gc.collect()
    y = base.copy(); y["high"] = y["high"] + 1000.0
    if id(y) == xid:
        hits += 1
        stale = np.allclose(wf.outcomes(y, 500, 500, "base")[1][0], r1, equal_nan=True)
        print("id reused at iter", k, "stale result returned:", stale); break
print("id reuse hits:", hits, "cache size:", len(wf._CACHE))
