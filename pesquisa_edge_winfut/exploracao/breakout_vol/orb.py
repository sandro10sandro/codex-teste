from fw import *
df = get_df()

def orb_signals(df, N, mode='mom', first_only=True, use_close=True):
    day = df['day'].values; mod = df['mod'].values
    h = df['high'].values; l = df['low'].values; c = df['close'].values
    sigs = []
    starts = np.flatnonzero(df['first_of_day'].values)
    ends = np.r_[starts[1:], len(df)]
    for s, e in zip(starts, ends):
        m = mod[s:e]
        inor = m < N
        if inor.sum() == 0 or (~inor).sum() == 0: continue
        orh = h[s:e][inor].max(); orl = l[s:e][inor].min()
        done_up = done_dn = False
        state = 0
        for k in np.flatnonzero(~inor):
            i = s + k
            px_up = c[i] if use_close else h[i]
            px_dn = c[i] if use_close else l[i]
            if px_up > orh and state != 1 and not done_up:
                sigs.append((i, 1 if mode == 'mom' else -1)); state = 1
                if first_only: done_up = True
            elif px_dn < orl and state != -1 and not done_dn:
                sigs.append((i, -1 if mode == 'mom' else 1)); state = -1
                if first_only: done_dn = True
            elif orl <= c[i] <= orh:
                state = 0
    return sigs

if __name__ == '__main__':
  res = []
  for N in (5, 15, 30, 60, 90):
      for mode in ('mom', 'fade'):
          for fo in (True, False):
              sg = orb_signals(df, N, mode, fo)
              g = grid(df, sg)
              g['N'] = N; g['mode'] = mode; g['fo'] = fo
              res.append(g)
  R = pd.concat(res)
  pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
  print(R.groupby(['N','mode','fo'])[['n','total','t']].agg({'n':'mean','total':['mean','max'],'t':['max']}))
  print(R[R.apply(passes, axis=1)])
  print('variants', VARIANTS[0])
  R.to_csv('orb.csv', index=False)
