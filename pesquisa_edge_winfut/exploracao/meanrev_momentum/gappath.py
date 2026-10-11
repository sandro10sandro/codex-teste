import sys; sys.path.insert(0,'.')
from base import *
df=get_df(); F=pd.read_pickle('F.pkl')
dopen=df.groupby('day').open.transform('first')
sg=np.sign(F.gap)
x=pd.DataFrame({'mod':df['mod'],'day':df.day,'v':sg*(df.close-dopen),'gap':F.gap.abs()})
p=x.pivot(index='day',columns='mod',values='v')
m=p.mean(); s=p.std()/np.sqrt(p.notna().sum())
for mm in (0,1,2,5,10,15,20,30,45,60,90,120,180,240,300,360,420,480,509):
    print(mm, round(m[mm],1), round(m[mm]/s[mm],2), ' h1',round(p.loc[:28,mm].mean(),1),' h2',round(p.loc[29:,mm].mean(),1))
