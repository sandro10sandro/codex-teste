from levels_lib import *
df = get()
h = df['high'].values; l = df['low'].values; c = df['close'].values
first = df['first_of_day'].values; mod = df['mod'].values

def hod_events(L, mode='touch', tmin=30):
    sigs = []
    for i in range(len(df)):
        if first[i]:
            H = h[i]; Lo = l[i]; tH = i; tL = i; continue
        if mode == 'touch':
            up = h[i] > H; dn = l[i] < Lo
        else:
            up = c[i] > H; dn = c[i] < Lo
        if up and i - tH >= L and mod[i] >= tmin: sigs.append((i, 1))
        if dn and i - tL >= L and mod[i] >= tmin: sigs.append((i, -1))
        if h[i] > H: H = h[i]; tH = i
        if l[i] < Lo: Lo = l[i]; tL = i
    return sigs

for L in (15, 30, 60, 120):
    for mode in ('touch', 'close'):
        evaluate(df, f'HODLOD break L{L} {mode}', hod_events(L, mode))
print('variants so far', total_count())
