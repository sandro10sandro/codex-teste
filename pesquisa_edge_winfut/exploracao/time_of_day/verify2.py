import warnings; warnings.filterwarnings('ignore')
import importlib.util
from ev import *
df=get()
out={}
for f in ['time_of_day_1','time_of_day_2']:
    spec=importlib.util.spec_from_file_location(f, f'/tmp/claude-0/-home-user-codex-teste/6018d537-360c-53a0-852b-fd7bc8336aa9/scratchpad/edge/candidates/{f}.py')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    sig=m.signals(df)
    tr,st=wf.backtest(df,sig,m.TARGET,m.STOP,'base')
    tr['month']=tr.date//100
    tr['week']=pd.to_datetime(tr.date.astype(str)).dt.isocalendar().week
    print(f,'by month',tr.groupby('month').pnl.agg(['count','sum']).round(0).to_dict('index'))
    wk=tr.groupby('week').pnl.sum()
    print('  weeks positive',(wk>0).sum(),'of',len(wk), wk.round(0).tolist())
    # sign-randomization at the same entry bars (single-trade version is exact; for multi it's approximate)
    o=wf.outcomes(df,m.TARGET,m.STOP,'base')
    if f=='time_of_day_2':
        e=tr.entry.values
        pl=o[1][0][e]; ps=o[-1][0][e]
        rng=np.random.default_rng(1)
        sims=np.array([np.where(rng.random(len(e))<0.5,pl,ps).sum() for _ in range(20000)])
        print('  sign-randomization p (same entry bars, random direction):',(sims>=tr.pnl.sum()).mean(), 'null mean',sims.mean().round(0))
        # all-long and all-short at the same bars
        print('  all-long same bars',pl.sum().round(0),' all-short',ps.sum().round(0))
    daily=tr.groupby('date').pnl.sum().reindex(sorted(df.date.unique()),fill_value=0)
    # bootstrap CI of mean daily pnl
    rng=np.random.default_rng(2)
    bs=[rng.choice(daily.values,len(daily)).mean() for _ in range(5000)]
    print('  daily mean %.0f, bootstrap 90%% CI [%.0f, %.0f]'%(daily.mean(),np.percentile(bs,5),np.percentile(bs,95)))
