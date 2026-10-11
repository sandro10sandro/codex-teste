from levels_lib import *
df = get(); f = features(df)
c = df['close'].values; h = df['high'].values; l = df['low'].values; o = df['open'].values
mod = df['mod'].values; first = df['first_of_day'].values; day = df['day'].values
pdh, pdl, pdc = f.pdh.values, f.pdl.values, f.pdc.values
dopen = f.dopen.values
# floor pivots
P = (pdh + pdl + pdc) / 3
R1 = 2 * P - pdl; S1 = 2 * P - pdh; R2 = P + (pdh - pdl); S2 = P - (pdh - pdl)
for nm, lv in [('P', P), ('R1', R1), ('S1', S1)]:
    evaluate(df, f'pivot {nm} touch', first_touch_sigs(df, lv, 'touch', require_open_side=False))
s = []
for lv in (R1, S1, R2, S2):
    s += first_touch_sigs(df, lv, 'touch', require_open_side=False)
evaluate(df, 'pivot R1S1R2S2 touch', s)

# gap fill event: gap >= g (pct); first touch of PDC; follow = continue in fill direction
gap = (dopen - pdc) / c * 100
for g in (0.2, 0.4):
    sg = []
    for i in range(len(df)):
        if first[i]:
            done = False
        if done or np.isnan(gap[i]) or abs(gap[i]) < g: continue
        if gap[i] > 0 and l[i] <= pdc[i]:
            sg.append((i, -1)); done = True
        elif gap[i] < 0 and h[i] >= pdc[i]:
            sg.append((i, 1)); done = True
    evaluate(df, f'gapfill touch g>={g}', sg)

# return to day open after excursion >= X pct; follow = continue in the return direction
for X in (0.3, 0.6):
    sg = []
    for i in range(len(df)):
        if first[i]:
            ex_up = ex_dn = False; done = False
            continue
        if done: continue
        if h[i] >= dopen[i] * (1 + X / 100): ex_up = True
        if l[i] <= dopen[i] * (1 - X / 100): ex_dn = True
        if ex_up and l[i] <= dopen[i] and mod[i] < 480:
            sg.append((i, -1)); done = True
        elif ex_dn and h[i] >= dopen[i] and mod[i] < 480:
            sg.append((i, 1)); done = True
    evaluate(df, f'return-to-open X{X}', sg)
print('variants so far', total_count())
