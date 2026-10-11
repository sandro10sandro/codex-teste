import sys, importlib.util
sys.path.insert(0, '/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/lib')
import wf, numpy as np
path = sys.argv[1]
spec = importlib.util.spec_from_file_location('cand', path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
df = wf.load()
sig = m.signals(df)
print(m.NAME, m.TARGET, m.STOP, 'signals', len(sig))
for T, S in [(m.TARGET, m.STOP)] + [(t, s) for t in (200,300,400,500) for s in (200,300,400,500) if (abs(t-m.TARGET)<=100 and abs(s-m.STOP)<=100) and (t, s) != (m.TARGET, m.STOP)]:
    tr, st = wf.backtest(df, sig, T, S, 'base')
    if (T, S) == (m.TARGET, m.STOP):
        trs, sts = wf.backtest(df, sig, T, S, 'stress')
        rb = wf.random_baseline(df, tr, T, S, 'base')
        print('MAIN', T, S, st, '\n stress total', sts['total'], 'random_baseline', rb)
    else:
        print('neighbor', T, S, {k: st[k] for k in ['n','total','t_daily','first_half_total','second_half_total']})
print('lookahead_check', wf.lookahead_check(m.signals, df))
print('deterministic', sig == m.signals(df))
