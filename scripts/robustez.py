"""Checagens de robustez das regras que pareceram melhores em abertura.py.

Uso:
    python3 scripts/robustez.py                    # usa WINFUT_20MB_1.csv da raiz do repositório
    python3 scripts/robustez.py parte1.csv parte2.csv ...

Divide o período em duas metades, piora o custo, retira os 5 melhores dias
e separa os dias por tamanho do gap.
"""
import collections
import statistics as st
import sys

from abertura import CSV_PADRAO, carregar, preparar, run, stats


def test(name, sig, T, S, subset, cost=10):
    res = [run(d, sig(d), T, S, cost) for d in subset if sig(d)]
    pn = [r[0] for r in res]
    n, wr, m, tot, dd, t = stats(pn)
    why = collections.Counter(r[1] for r in res)
    top5 = sum(sorted(pn, reverse=True)[:5])
    print(f"  {name:28s} n={n:3d} acerto={wr:5.1f}% média={m:6.1f} total={tot:6.0f} t={t:5.2f} | saídas {dict(why)} | total sem 5 melhores dias={tot-top5:6.0f}")


def main(caminhos):
    info = preparar(carregar(caminhos))
    agree = sum(1 for d in info if d['mom'] and d['gap'] and d['mom'] == -d['gap'])
    both = sum(1 for d in info if d['mom'] and d['gap'])
    print(f"Momentum 2min concorda com 'contra o gap' em {agree}/{both} dias ({agree/both*100:.0f}%)\n")

    h = len(info) // 2
    for label, sub in [('1ª metade', info[:h]), ('2ª metade', info[h:]), ('Período todo', info)]:
        print(f"{label} ({sub[0]['day']} a {sub[-1]['day']})")
        test('Contra o gap 0.30/0.30', lambda d: -d['gap'], 0.30, 0.30, sub)
        test('Contra o gap 0.20/0.20', lambda d: -d['gap'], 0.20, 0.20, sub)
        test('Momentum 2min 0.20/0.20', lambda d: d['mom'], 0.20, 0.20, sub)
    print("\nCusto 20 pts/op (slippage pior), período todo")
    test('Contra o gap 0.30/0.30', lambda d: -d['gap'], 0.30, 0.30, info, 20)
    test('Contra o gap 0.20/0.20', lambda d: -d['gap'], 0.20, 0.20, info, 20)
    test('Momentum 2min 0.20/0.20', lambda d: d['mom'], 0.20, 0.20, info, 20)

    gaps = sorted(((d['gap_pct'], d) for d in info if d['gap_pct'] is not None), key=lambda x: x[0])
    print(f"\nGap absoluto: mediana {st.median(g for g, _ in gaps):.2f}%")
    for label, sub in [('gaps pequenos (metade inferior)', [d for _, d in gaps[:len(gaps)//2]]),
                       ('gaps grandes (metade superior)', [d for _, d in gaps[len(gaps)//2:]])]:
        print(label)
        test('Contra o gap 0.30/0.30', lambda d: -d['gap'], 0.30, 0.30, sub)


if __name__ == '__main__':
    main(sys.argv[1:] or [CSV_PADRAO])
