import warnings; warnings.filterwarnings('ignore')
import importlib.util, sys
from ev import *
df=wf.load()   # fresh load, not cached pickle
for f in ['time_of_day_1','time_of_day_2']:
    spec=importlib.util.spec_from_file_location(f, f'/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/candidates/{f}.py')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    sig=m.signals(df); sig2=m.signals(df)
    tr,st=wf.backtest(df,sig,m.TARGET,m.STOP,'base')
    rb=wf.random_baseline(df,tr,m.TARGET,m.STOP,'base')
    ss=wf.backtest(df,sig,m.TARGET,m.STOP,'stress')[1]
    zz=wf.backtest(df,sig,m.TARGET,m.STOP,'zero')[1]
    la=wf.lookahead_check(m.signals,df)
    print(f, m.NAME, m.TARGET, m.STOP, 'deterministic', sig==sig2)
    print(' base', st)
    print(' random', rb, ' stress total', ss['total'], 't', ss['t_daily'], ' zero total', zz['total'], ' lookahead_ok', la)
    # neighbours in TS
    for t,s in [(400,500),(500,400),(400,400),(300,500)]:
        x=wf.backtest(df,sig,t,s,'base')[1]; print('   nb',t,s,x['total'],x['t_daily'],x['first_half_total'],x['second_half_total'])
