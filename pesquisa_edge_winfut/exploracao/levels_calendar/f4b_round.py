from levels_lib import *
df = get()
rh = df['real_high'].values; rl = df['real_low'].values; rc = df['real_close'].values; ro = df['real_open'].values
first = df['first_of_day'].values; mod = df['mod'].values

def round_touch_events(G):
    """return list of (i, a, level) first touch of each grid level per day per direction"""
    ev = []; used = set()
    for i in range(len(df)):
        if first[i]: used = set(); prev = ro[i]
        else: prev = rc[i-1]
        k_lo = np.floor(prev / G) + 1; k_hi = np.floor(rh[i] / G)
        if k_hi >= k_lo:
            k = k_lo
            if (k, 1) not in used: used.add((k, 1)); ev.append((i, 1, k * G))
        k_hi2 = np.ceil(prev / G) - 1; k_lo2 = np.ceil(rl[i] / G)
        if k_hi2 >= k_lo2:
            k = k_hi2
            if (k, -1) not in used: used.add((k, -1)); ev.append((i, -1, k * G))
    return ev

for G in (500, 1000):
    ev = round_touch_events(G)
    # rejection: close back on approach side; break: close beyond
    rej = [(i, a) for i, a, L in ev if (rc[i] - L) * a < 0]
    brk = [(i, a) for i, a, L in ev if (rc[i] - L) * a >= 0]
    print(G, 'events', len(ev), 'rej', len(rej), 'brk', len(brk))
    evaluate(df, f'round G{G} touch-reject', rej)
    evaluate(df, f'round G{G} touch-closebeyond', brk)
print('variants so far', total_count())
