import sys; sys.path.insert(0,'.')
from base import *
df=get_df()
def px(mod, col='close'):
    s=df[df['mod']==mod].set_index('day')[col]; return s
g=df.groupby('day')
D=pd.DataFrame({'o':g.open.first(),'c':g.close.last()})
D['pc']=D.c.shift()
for m in (0,14,29,59,89,119,179,239,299,359,419,449,479,509): D[f'c{m}']=px(m)
D['c509']=D['c509'].fillna(g.close.last())
D['gap']=D.o-D.pc
D['on30']=D.c29-D.pc       # prev close -> 9:30
D['f30']=D.c29-D.o
D['f60']=D.c59-D.o
D['on60']=D.c59-D.pc
D['cash30']=D.c89-D.c59   # 10:00->10:30
D['am']=D.c179-D.o
y={'L30':D.c509-D.c479,'L60':D.c509-D.c449,'b17':D.c479-D.c419,'pm':D.c509-D.c299,'rest60':D.c509-D.c59,'rest90':D.c509-D.c89,'rest_gap':D.c509-D.o}
rows=[]
for xf in ['gap','on30','f30','f60','on60','cash30','am']:
    for yn,yy in y.items():
        m=D[xf].notna()&yy.notna()
        x=D[xf][m]; v=yy[m]
        r=np.corrcoef(x,v)[0,1]
        # sign strategy: trade sign(x) -> pnl = sign(x)*v (zero cost)
        p=np.sign(x)*v
        t=p.mean()/(p.std()/np.sqrt(len(p)))
        h=len(p)//2
        rows.append((xf,yn,round(r,2),round(p.mean(),1),round(t,2),round(p[:h].sum()),round(p[h:].sum())))
pd.set_option('display.width',200)
print(pd.DataFrame(rows,columns=['x','y','corr','signpnl','t','h1','h2']).to_string())
