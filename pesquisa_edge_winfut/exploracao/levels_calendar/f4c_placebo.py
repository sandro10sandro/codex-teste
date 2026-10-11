from levels_lib import *
df = get()
rh = df['real_high'].values; rl = df['real_low'].values; rc = df['real_close'].values; ro = df['real_open'].values
first = df['first_of_day'].values
def ev_grid(G, off):
    ev = []; used = set()
    for i in range(len(df)):
        if first[i]: used = set(); prev = ro[i]
        else: prev = rc[i-1]
        k_lo = np.floor((prev-off) / G) + 1; k_hi = np.floor((rh[i]-off) / G)
        if k_hi >= k_lo and (k_lo, 1) not in used: used.add((k_lo, 1)); ev.append((i, 1))
        k_hi2 = np.ceil((prev-off) / G) - 1; k_lo2 = np.ceil((rl[i]-off) / G)
        if k_hi2 >= k_lo2 and (k_hi2, -1) not in used: used.add((k_hi2, -1)); ev.append((i, -1))
    return ev
for off in (0, 125, 250, 375, 500, 625, 750, 875):
    evaluate(df, f'grid1000 off{off} touch', ev_grid(1000, off), orient=(-1,))
print('variants so far', total_count())
