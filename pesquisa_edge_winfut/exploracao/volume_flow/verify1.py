import sys, importlib.util
sys.path.insert(0,"/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/lib")
import wf
spec = importlib.util.spec_from_file_location('c1', '/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/candidates/volume_flow_1.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
df = wf.load()
sg = m.signals(df)
tr, st = wf.backtest(df, sg, m.TARGET, m.STOP, 'base')
trs, sts = wf.backtest(df, sg, m.TARGET, m.STOP, 'stress')
rb = wf.random_baseline(df, tr, m.TARGET, m.STOP, 'base')
print(m.NAME, st)
print('stress', sts['total'], 'p', rb)
print('lookahead', wf.lookahead_check(m.signals, df))
print('deterministic', m.signals(df) == sg)
