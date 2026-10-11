from ev import *
df=get()
day=df.day.values; mod=df['mod'].values; cl=df.close.values
dopen=df.groupby('day').open.transform('first').values
# direction per day from first k bars
def sig_fade_all(k, E, sign=-1):
    ck = pd.Series(np.where(mod==k, cl, np.nan)).groupby(day).transform('max').values  # close at bar k of same day (available only after bar k)
    out=[]
    for i in np.flatnonzero((mod>=max(E,k)) & (mod<=479)):
        d=np.sign(ck[i]-dopen[i])
        if d!=0 and not np.isnan(d): out.append((int(i), int(sign*d)))
    return out
res=[]
for k in [2,4,9]:
    for E in [29,89,179]:
        R=grid(df, sig_fade_all(k,E), show=False); R['k']=k; R['E']=E; res.append(R)
R=pd.concat(res)
print(R.pivot_table(index=['k','E'],columns='t_s',values='total').round(0).to_string())
print(R.pivot_table(index=['k','E'],columns='t_s',values='t_daily').round(1).to_string())
print(R.pivot_table(index=['k','E'],columns='t_s',values='n').round(0).to_string())
