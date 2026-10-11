"""Testa o 'operacional de 15 minutos' com ENTRADA ÀS 9:15: lê 9:00-9:14, entra na abertura do
candle de 9:15 e sai no alvo, no stop ou no fechamento de 9:29 (= 9:30).

Uso:
    python3 scripts/entrada_0915.py WINFUT_NA_BMF_I_v6_raw.csv [outros.csv ...]

Regras e grade definidas ANTES de rodar, todas reportadas:
  - sinais conhecidos às 9:15: momentum 15 min (fechamento de 9:14 acima/abaixo da abertura),
    reversão desse momentum, segue o gap, contra o gap, sempre comprado, sempre vendido;
  - alvo/stop na mesma grade de abertura.py (0,20/0,20, 0,30/0,15, 0,15/0,30, 0,30/0,30), custo 10;
  - mais uma regra de rompimento: compra quando um candle a partir de 9:15 supera a máxima de
    9:00-9:14, vende quando perde a mínima; entrada no nível rompido (ou na abertura do candle, se
    ele já abriu além), stop no outro extremo da faixa, alvo = 1x a faixa, saída no máximo no
    fechamento de 9:59; candle que rompe os dois lados ao mesmo tempo = dia sem operação.
Na série WIN$N os dias de rolagem e os dias após buraco ficam sem operação nos sinais de gap.
Isto é uma busca em 25 combinações no período inteiro: resultado positivo aqui é hipótese, não
evidência. Por isso o período é dividido em duas metades e as duas são mostradas lado a lado.
"""
import collections
import random
import statistics as st
import sys

from abertura import COST, GRADE, carregar, factor, run, sinal, stats
from fora_da_amostra import BURACO_MAX, avaliar, data, dias_de_rolagem, linha

SINAIS = {
    'Momentum 15min (segue 9:00-9:14)': lambda d: d['mom'],
    'Reversão 15min (contra 9:00-9:14)': lambda d: -d['mom'],
    'Segue o gap':                       lambda d: d['gap'],
    'Contra o gap':                      lambda d: -d['gap'],
    'Sempre comprado':                   lambda d: 1,
    'Sempre vendido':                    lambda d: -1,
}


def preparar_0915(days):
    """Leitura = 9:00-9:14 (começando até 9:10), entrada no candle de 9:15, saída até 9:29."""
    keys = list(days)
    info = []
    for i, k in enumerate(keys):
        bars = days[k]
        leitura = [b for b in bars if 90000 <= b['t'] <= 91400]
        trade = [b for b in bars if 91500 <= b['t'] <= 92900]
        depois = [b for b in bars if 91500 <= b['t'] <= 95900]
        if len(leitura) < 10 or len(trade) < 10 or leitura[0]['t'] > 91000 or trade[0]['t'] != 91500:
            continue
        prev_close = days[keys[i - 1]][-1]['c'] if i > 0 else None
        info.append(dict(day=k, f=factor(bars), bars=bars, win=leitura, trade=trade, depois=depois,
                         hi=max(b['h'] for b in leitura), lo=min(b['l'] for b in leitura),
                         mom=sinal(leitura[-1]['c'] - leitura[0]['o']),
                         gap=sinal(leitura[0]['o'] - prev_close) if prev_close else 0))
    return info


def rompimento(d, cost=COST):
    """Primeiro candle a partir de 9:15 que supera a máxima ou perde a mínima de 9:00-9:14."""
    hi, lo, f = d['hi'], d['lo'], d['f']
    faixa = hi - lo
    for j, b in enumerate(d['depois']):
        up, dn = b['h'] > hi, b['l'] < lo
        if up and dn:
            return None
        if up or dn:
            direction = 1 if up else -1
            e = max(b['o'], hi) if up else min(b['o'], lo)
            tgt = e + direction * faixa
            stp = lo if up else hi
            for bb in d['depois'][j:]:
                if (bb['l'] <= stp) if direction > 0 else (bb['h'] >= stp):
                    return (stp - e) * direction / f - cost, 'stop', bb['t']
                if (bb['h'] >= tgt) if direction > 0 else (bb['l'] <= tgt):
                    return (tgt - e) * direction / f - cost, 'alvo', bb['t']
            return (d['depois'][-1]['c'] - e) * direction / f - cost, 'tempo', d['depois'][-1]['t']
    return None


def avaliar_rompimento(sub, cost=COST):
    res = [r for r in (rompimento(d, cost) for d in sub) if r]
    if not res:
        return None
    n, wr, m, tot, dd, t = stats([r[0] for r in res])
    return dict(n=n, wr=wr, m=m, tot=tot, dd=dd, t=t, saidas=collections.Counter(r[1] for r in res))


def resumo(r):
    return "   (sem op.)   " if r is None else f"n={r['n']:4d} média={r['m']:6.1f} t={r['t']:5.2f}"


def main(caminhos):
    days = carregar(caminhos)
    ds = list(days)
    anterior = {ds[i]: ds[i - 1] for i in range(1, len(ds))}
    info = preparar_0915(days)
    rol = dias_de_rolagem(days)
    excl = collections.Counter()
    for d in info:
        if d['day'] in rol:
            d['gap'] = 0; excl['rolagem'] += 1
        elif d['day'] in anterior and (data(d['day']) - data(anterior[d['day']])).days > BURACO_MAX:
            d['gap'] = 0; excl['buraco'] += 1
    print(f"Pregões no arquivo: {len(ds)} ({ds[0]} a {ds[-1]}). Avaliáveis às 9:15: {len(info)} "
          f"(leitura 9:00-9:14 com >=10 candles começando até 9:10, candle de 9:15 presente, >=10 candles até 9:29)")
    print("Avaliáveis por ano:", dict(sorted(collections.Counter(d['day'][:4] for d in info).items())))
    print(f"Sem operação nos sinais de gap: rolagem {excl['rolagem']}, buraco de dados {excl['buraco']}")

    # ---------- 1. Janela 9:15-9:29 vs 9:00-9:14 ----------
    r1 = [(max(b['h'] for b in d['win']) - min(b['l'] for b in d['win'])) / d['f'] for d in info]
    r2 = [(max(b['h'] for b in d['trade']) - min(b['l'] for b in d['trade'])) / d['f'] for d in info]
    q1 = st.mean(b['q'] for d in info for b in d['win'])
    q2 = st.mean(b['q'] for d in info for b in d['trade'])
    lvl = st.mean(d['trade'][0]['o'] / d['f'] for d in info)
    print(f"\n1) Amplitude mediana: 9:00-9:14 {st.median(r1):.0f} pts | 9:15-9:29 {st.median(r2):.0f} pts. "
          f"Contratos/min: {q1:.0f} | {q2:.0f}. Nível médio {lvl:,.0f} pts (0,30% ≈ {lvl * 0.003:.0f} pts)")

    # ---------- 2. Grade ----------
    h = len(info) // 2
    m1, m2 = info[:h], info[h:]
    print(f"\n2) Entrada na abertura de 9:15, saída alvo/stop ou 9:30, custo {COST}. "
          f"Período todo | 1ª metade ({m1[0]['day']} a {m1[-1]['day']}) | 2ª metade ({m2[0]['day']} a {m2[-1]['day']})")
    print(f"   {'regra':34s} {'alvo/stop':>9s}  {'todo':^30s} | {'1ª metade':^30s} | {'2ª metade':^30s}")
    for nome, sig in SINAIS.items():
        for T, S in GRADE:
            print(f"   {nome:34s} {T:.2f}/{S:.2f}  {resumo(avaliar(sig, T, S, info))} | "
                  f"{resumo(avaliar(sig, T, S, m1))} | {resumo(avaliar(sig, T, S, m2))}")

    # ---------- 2b. Sem custo: o sinal tem informação? ----------
    print(f"\n2b) Sem custo nenhum, alvo/stop 0,30/0,30 (só para ver se algum sinal tem informação; "
          f"edge bruto abaixo de ~15 pts não paga custo real):")
    for nome, sig in SINAIS.items():
        print(f"   {nome:34s}  {resumo(avaliar(sig, 0.30, 0.30, info, 0))} | "
              f"{resumo(avaliar(sig, 0.30, 0.30, m1, 0))} | {resumo(avaliar(sig, 0.30, 0.30, m2, 0))}")

    # ---------- 3. Rompimento ----------
    print("\n3) Rompimento da faixa 9:00-9:14 (stop no outro extremo, alvo 1x a faixa, até 9:59):")
    for rotulo, sub in (('todo', info), ('1ª metade', m1), ('2ª metade', m2)):
        r = avaliar_rompimento(sub)
        print(linha(f"Rompimento, {rotulo}", r) if r else f"   Rompimento, {rotulo}: sem operações")
    faixa = [(d['hi'] - d['lo']) / d['f'] for d in info]
    print(f"   faixa 9:00-9:14 mediana {st.median(faixa):.0f} pts; dias com rompimento até 9:59: "
          f"{sum(1 for d in info if rompimento(d))} de {len(info)}")

    # ---------- 4. Por ano, só para o que passou de t >= 2 no período todo ----------
    print("\n4) Por ano, média por operação (só regras com t >= 2 no período todo):")
    anos = collections.OrderedDict()
    for d in info:
        anos.setdefault(d['day'][:4], []).append(d)
    candidatos = [(f"{nome} {T:.2f}/{S:.2f}", lambda sub, s=sig, T=T, S=S: avaliar(s, T, S, sub))
                  for nome, sig in SINAIS.items() for T, S in GRADE]
    candidatos.append(("Rompimento", avaliar_rompimento))
    algum = False
    for rotulo, fn in candidatos:
        r = fn(info)
        if r is None or r['t'] < 2:
            continue
        algum = True
        print(f"   {rotulo}: " + "  ".join(f"{a} {fn(sub)['m']:+.0f}" if fn(sub) else f"{a} -" for a, sub in anos.items()))
    if not algum:
        print("   nenhuma regra positiva com t >= 2")

    # ---------- 5. Base aleatória ----------
    random.seed(42)
    tots = sorted(sum(run(d, random.choice((1, -1)), 0.30, 0.30)[0] for d in info) for _ in range(1000))
    print(f"\n5) Base aleatória (cara/coroa às 9:15, 0,30/0,30, custo {COST}, 1.000 simulações de {len(info)} dias): "
          f"média por op. p5 {tots[50] / len(info):.1f} | mediana {tots[500] / len(info):.1f} | p95 {tots[950] / len(info):.1f}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit("Informe o CSV, ex.: python3 scripts/entrada_0915.py WINFUT_NA_BMF_I_v6_raw.csv")
    main(sys.argv[1:])
