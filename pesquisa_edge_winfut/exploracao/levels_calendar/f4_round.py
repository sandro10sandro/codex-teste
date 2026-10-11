from levels_lib import *
df = get()
rh = df['real_high'].values; rl = df['real_low'].values; rc = df['real_close'].values; ro = df['real_open'].values
first = df['first_of_day'].values; mod = df['mod'].values; tick = df['tick'].values
fac = tick / 5.0

def round_sigs(G, mode='touch', margin_real=0.0, once=True, tmin=0, tmax=480):
    """first touch of each grid level per day. follow orientation."""
    sigs = []; used = set()
    for i in range(len(df)):
        if first[i]:
            used = set(); prev = ro[i]
        else:
            prev = rc[i-1]
        if not (tmin <= mod[i] <= tmax):
            continue
        if mode == 'touch':
            # levels crossed upward: prev < k*G <= high
            k_lo = np.floor(prev / G) + 1; k_hi = np.floor(rh[i] / G)
            for k in np.arange(k_lo, k_hi + 1):
                if (k, 1) not in used or not once:
                    used.add((k, 1)); sigs.append((i, 1)); break
            k_hi2 = np.ceil(prev / G) - 1; k_lo2 = np.ceil(rl[i] / G)
            for k in np.arange(k_hi2, k_lo2 - 1, -1):
                if (k, -1) not in used or not once:
                    used.add((k, -1)); sigs.append((i, -1)); break
        else:
            m = margin_real
            k_lo = np.floor((prev - m) / G) + 1; k_hi = np.floor((rc[i] - m) / G)
            for k in np.arange(k_lo, k_hi + 1):
                if (k, 1) not in used or not once:
                    used.add((k, 1)); sigs.append((i, 1)); break
            k_hi2 = np.ceil((prev + m) / G) - 1; k_lo2 = np.ceil((rc[i] + m) / G)
            for k in np.arange(k_hi2, k_lo2 - 1, -1):
                if (k, -1) not in used or not once:
                    used.add((k, -1)); sigs.append((i, -1)); break
    return sigs

for G in (250, 500, 1000):
    for mode, m in [('touch', 0), ('close', 0), ('close', 50)]:
        s = round_sigs(G, mode, m)
        evaluate(df, f'round G{G} {mode} m{m}', s)
print('variants so far', total_count())
