import warnings; warnings.filterwarnings('ignore')
from ev import *
df=get()
day=df.day.values; mod=df['mod'].values; cl=df.close.values
dopen=df.groupby('day').open.transform('first').values
def sigO(S,E):
    return [(int(i),int(-np.sign(cl[i]-dopen[i]))) for i in np.flatnonzero((mod>=S)&(mod<E)) if cl[i]!=dopen[i]]
for (S,E),(t,s) in [((60,90),(400,500)),((60,90),(500,500)),((70,90),(500,500)),((65,90),(500,500)),((60,90),(300,300))]:
    sig=sigO(S,E)
    tr,st=wf.backtest(df,sig,t,s,'base')
    rb=wf.random_baseline(df,tr,t,s,'base')
    st2=wf.backtest(df,sig,t,s,'stress')[1]
    print((S,E),(t,s),{k:st[k] for k in ['n','total','avg','win_rate','t_daily','first_half_total','second_half_total','long_total','short_total','targets','stops','eod','max_dd','pct_days_pos']}, 'p',rb, 'stress',st2['total'])
    tr['month']=tr.date//100
    print('  by month', tr.groupby('month').pnl.agg(['count','sum']).round(0).to_dict())
    daily=tr.groupby('date').pnl.sum().sort_values()
    print('  trades/day', round(len(tr)/tr.date.nunique(),2), 'days traded', tr.date.nunique(), ' top5 days', daily.tail(5).round(0).tolist(), 'worst5', daily.head(5).round(0).tolist())
    print('  total ex top3 days', round(daily.iloc[:-3].sum()), ' ex top5', round(daily.iloc[:-5].sum()))
    print('  entry minute dist', (tr.time//100).value_counts().sort_index().to_dict())
    print('  pnl by trade# in day', tr.groupby(tr.groupby('date').cumcount()).pnl.agg(['count','sum','mean']).round(0).to_dict())
