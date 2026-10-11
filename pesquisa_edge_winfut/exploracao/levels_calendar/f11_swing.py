from levels_lib import *
df = get()
c = df['close'].values; h = df['high'].values; l = df['low'].values
mod = df['mod'].values; first = df['first_of_day'].values; day = df['day'].values; n = len(df)
tick = df['tick'].values
def swing_sigs(N, mode):
    """intraday fractal pivots confirmed N bars later. Event: first touch (high>=pivot high) of the most recent
    unbroken swing high from below / swing low from above. follow = break direction."""
    s = []
    for dd, idx in df.groupby('day').indices.items():
        idx = np.sort(idx)
        highs = []; lows = []   # active levels
        for j, i in enumerate(idx):
            # confirm pivot at position j-N
            p = j - N
            if p >= N:
                ip = idx[p]
                win = idx[p - N: p + N + 1]
                if h[ip] == h[win].max() and (h[win] == h[ip]).sum() == 1: highs.append(h[ip])
                if l[ip] == l[win].min() and (l[win] == l[ip]).sum() == 1: lows.append(l[ip])
            if j == 0: continue
            # check touches of active levels
            hit_up = [L for L in highs if (h[i] >= L if mode == 'touch' else c[i] > L) and c[i-1] < L]
            hit_dn = [L for L in lows if (l[i] <= L if mode == 'touch' else c[i] < L) and c[i-1] > L]
            if hit_up: s.append((i, 1))
            if hit_dn: s.append((i, -1))
            # levels broken (traded through) are removed
            highs = [L for L in highs if h[i] < L]
            lows = [L for L in lows if l[i] > L]
    return s
for N in (5, 10, 20):
    for mode in ('touch', 'close'):
        evaluate(df, f'swing N{N} {mode}', swing_sigs(N, mode))
print('variants so far', total_count())
