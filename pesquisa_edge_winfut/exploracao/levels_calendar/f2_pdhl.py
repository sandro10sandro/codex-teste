from levels_lib import *
df = get(); f = features(df)
pdh = f['pdh'].values; pdl = f['pdl'].values; pdc = f['pdc'].values; pdo = f['pdo'].values
mid = (pdh + pdl) / 2
for nm, lv in [('PDH', pdh), ('PDL', pdl)]:
    for mode, m in [('touch', 0), ('close', 0), ('close', 150)]:
        evaluate(df, f'{nm} {mode} m{m}', first_touch_sigs(df, lv, mode, m))
# both together
for mode, m in [('touch', 0), ('close', 0), ('close', 150)]:
    s = first_touch_sigs(df, pdh, mode, m) + first_touch_sigs(df, pdl, mode, m)
    evaluate(df, f'PDH+PDL {mode} m{m}', s)
for nm, lv in [('PDC', pdc), ('PDO', pdo), ('PDmid', mid)]:
    for mode, m in [('touch', 0), ('close', 150)]:
        evaluate(df, f'{nm} {mode} m{m}', first_touch_sigs(df, lv, mode, m, require_open_side=False))
print('variants so far', total_count())
