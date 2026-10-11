from ev import *
df=get()
day=df.day.values; mod=df['mod'].values; cl=df.close.values
dopen=df.groupby('day').open.transform('first').values
def sig_fade(k, sign=-1):
    idx=np.flatnonzero(mod==k)
    return [(int(i), int(sign*np.sign(cl[i]-dopen[i]))) for i in idx if cl[i]!=dopen[i]]
res=[]
for k in [0,2,4,6,9,14,19,29]:
    for sign in (-1,1):
        R=grid(df, sig_fade(k,sign), show=False)
        R['k']=k; R['sign']=sign; res.append(R)
R=pd.concat(res)
piv=R.pivot_table(index=['k','sign'],columns='t_s',values='total')
print(piv.round(0).to_string())
piv=R.pivot_table(index=['k','sign'],columns='t_s',values='t_daily')
print(piv.round(1).to_string())
