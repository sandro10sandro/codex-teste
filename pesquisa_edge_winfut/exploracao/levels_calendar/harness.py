from feat import *
import json
TS = [(T, S) for T in (200, 300, 400, 500) for S in (200, 300, 400, 500)]
VCOUNT_FILE = os.path.join(os.path.dirname(__file__), 'variants_count.txt')
RES_FILE = os.path.join(os.path.dirname(__file__), 'results.jsonl')

def add_count(k):
    with open(VCOUNT_FILE, 'a') as fh: fh.write(f'{k}\n')

def total_count():
    if not os.path.exists(VCOUNT_FILE): return 0
    return sum(int(x) for x in open(VCOUNT_FILE).read().split())

def evaluate(df, name, sigs, orient=(1, -1), TS=TS, show=True, minn=1):
    """sigs in 'follow' orientation; orient 1 = follow, -1 = fade"""
    rows = []
    for o in orient:
        s2 = [(i, d * o) for i, d in sigs]
        for T, S in TS:
            E, D, Pn = fastbt(df, s2, T, S, 'base')
            r = st(df, E, D, Pn)
            r.update(name=name, orient='follow' if o == 1 else 'fade', T=T, S=S)
            rows.append(r)
    add_count(len(rows))
    with open(RES_FILE, 'a') as fh:
        for r in rows:
            fh.write(json.dumps({k: (float(v) if isinstance(v, (np.floating, np.integer)) else v) for k, v in r.items()}) + '\n')
    if show:
        for o in ('follow', 'fade'):
            rr = [r for r in rows if r['orient'] == o]
            if not rr: continue
            n = rr[0]['n']
            ts = ' '.join(f"{r['t']:+.1f}" for r in rr)
            best = max(rr, key=lambda r: r['t'])
            print(f"{name:40s} {o:6s} n~{n:4d} t[16]: {ts} | best {best['T']}/{best['S']} tot {best['total']:.0f} t {best['t']} h {best['h1']:.0f}/{best['h2']:.0f}")
    return rows
