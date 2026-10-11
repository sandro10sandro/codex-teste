"""Testa o 'operacional de 15 minutos' (9:00-9:15) no WINFUT com candles de 1 minuto.

Uso:
    python3 scripts/abertura.py                    # usa WINFUT_20MB_1.csv da raiz do repositório
    python3 scripts/abertura.py parte1.csv parte2.csv ...

Formato esperado (exportação do Profit):
    <ticker>,<date>,<time>,<trades>,<close>,<low>,<high>,<open>,<vol>,<qty>,<aft>

A série WIN$D é ajustada multiplicativamente -> converte para pontos reais via tick (5 pts).
Só usa a biblioteca padrão do Python.
"""
import collections
import csv
import math
import random
import statistics as st
import sys
from pathlib import Path

CSV_PADRAO = Path(__file__).resolve().parent.parent / 'WINFUT_20MB_1.csv'
COST = 10  # pontos por ida+volta (≈1 tick de slippage na entrada + 1 na saída/stop; taxas ~ desprezíveis em pts)

# Regras definidas a priori (todas reportadas) e grade de alvo/stop em % do preço de entrada.
SINAIS = {
    'Momentum 2min (segue 9:00-9:02)': lambda d: d['mom'],
    'Reversão 2min (contra 9:00-9:02)': lambda d: -d['mom'],
    'Segue o gap':                      lambda d: d['gap'],
    'Contra o gap':                     lambda d: -d['gap'],
    'Sempre comprado':                  lambda d: 1,
    'Sempre vendido':                   lambda d: -1,
}
GRADE = [(0.20, 0.20), (0.30, 0.15), (0.15, 0.30), (0.30, 0.30)]


def carregar(caminhos):
    """Lê um ou mais CSVs e agrupa os candles por dia.

    Arquivos fatiados (um dia cortado entre dois arquivos) são unidos; linhas repetidas
    de (data, hora) são descartadas e candles de after-market ignorados."""
    barras = {}
    for caminho in caminhos:
        with open(caminho, newline='') as fh:
            for r in csv.DictReader(fh):
                if r['<aft>'] == 'S':
                    continue
                barras[(r['<date>'], int(r['<time>']))] = dict(
                    t=int(r['<time>']), o=float(r['<open>']), h=float(r['<high>']),
                    l=float(r['<low>']), c=float(r['<close>']), q=int(r['<qty>']))
    days = collections.OrderedDict()
    for (dia, _), b in sorted(barras.items()):
        days.setdefault(dia, []).append(b)
    return days


def factor(bars):
    """Fator de ajuste do dia: menor diferença entre preços distintos = 1 tick = 5 pontos."""
    ps = sorted(set(round(x, 6) for b in bars for x in (b['o'], b['h'], b['l'], b['c'])))
    return min(b - a for a, b in zip(ps, ps[1:])) / 5.0


def sinal(x):
    return math.copysign(1, x) if x else 0


def preparar(days):
    """Separa a janela 9:00-9:15 de cada dia e calcula os sinais conhecidos às 9:02."""
    keys = list(days)
    info = []
    for i, k in enumerate(keys):
        bars = days[k]
        f = factor(bars)
        win = [b for b in bars if 90000 <= b['t'] <= 91400]
        first2 = [b for b in win if b['t'] <= 90100]
        trade = [b for b in win if b['t'] >= 90200]
        if len(first2) < 1 or len(trade) < 5:
            continue
        prev_close = days[keys[i-1]][-1]['c'] if i > 0 else None
        info.append(dict(day=k, f=f, bars=bars, win=win, trade=trade,
                         mom=sinal(first2[-1]['c'] - win[0]['o']),
                         gap=sinal(win[0]['o'] - prev_close) if prev_close else 0,
                         gap_pct=abs(win[0]['o'] / prev_close - 1) * 100 if prev_close else None))
    return info


def run(d, direction, tgt_pct, stp_pct, cost=COST):
    """Entra na abertura do candle de 9:02, sai no alvo/stop ou no fechamento de 9:14 (=9:15)."""
    tr = d['trade']; e = tr[0]['o']; f = d['f']
    tgt = e * (1 + direction * tgt_pct / 100); stp = e * (1 - direction * stp_pct / 100)
    for b in tr:
        hit_t = b['h'] >= tgt if direction > 0 else b['l'] <= tgt
        hit_s = b['l'] <= stp if direction > 0 else b['h'] >= stp
        if hit_s:            # stop e alvo no mesmo candle -> assume stop (conservador)
            return (stp - e) * direction / f - cost, 'stop', b['t']
        if hit_t:
            return (tgt - e) * direction / f - cost, 'alvo', b['t']
    return (tr[-1]['c'] - e) * direction / f - cost, 'tempo', tr[-1]['t']


def stats(pnls):
    """(n, acerto %, média, total, drawdown máximo, estatística t da média)."""
    n = len(pnls); m = st.mean(pnls); sd = st.pstdev(pnls)
    eq = 0; peak = 0; dd = 0
    for p in pnls:
        eq += p; peak = max(peak, eq); dd = min(dd, eq - peak)
    return n, sum(p > 0 for p in pnls) / n * 100, m, sum(pnls), dd, (m / (sd / math.sqrt(n)) if sd else 0)


def main(caminhos):
    info = preparar(carregar(caminhos))
    print(f"Dias úteis testados: {len(info)}  ({info[0]['day']} a {info[-1]['day']})")
    lvl = st.mean(d['trade'][0]['o'] / d['f'] for d in info)
    print(f"Nível médio do WIN no período: {lvl:,.0f} pts  (0,25% ≈ {lvl*0.0025:.0f} pts)\n")

    # ---------- 1. Características da janela 9:00-9:15 ----------
    rng15 = [(max(b['h'] for b in d['win']) - min(b['l'] for b in d['win'])) / d['f'] for d in info]
    rngday = [(max(b['h'] for b in d['bars']) - min(b['l'] for b in d['bars'])) / d['f']
              for d in info if len(d['bars']) > 400]  # ignora dias incompletos
    mv = [abs(d['trade'][-1]['c'] - d['trade'][0]['o']) / d['f'] for d in info]
    print("1) Janela 9:00-9:15")
    print(f"   Amplitude 9:00-9:15: mediana {st.median(rng15):.0f} pts | média {st.mean(rng15):.0f} | p10 {sorted(rng15)[len(rng15)//10]:.0f} | p90 {sorted(rng15)[len(rng15)*9//10]:.0f}")
    print(f"   Amplitude do dia inteiro: mediana {st.median(rngday):.0f} pts  -> janela = {st.median(rng15)/st.median(rngday)*100:.0f}% do range diário (mediana)")
    print(f"   |9:02 -> 9:15| deslocamento líquido: mediana {st.median(mv):.0f} pts\n")

    # ---------- 2. Volume/volatilidade por faixa de horário ----------
    print("2) Volume e volatilidade por faixa de 15 min (média por minuto)")
    buckets = collections.defaultdict(lambda: [[], []])
    for d in info:
        for b in d['bars']:
            hh, mm = b['t'] // 10000, (b['t'] // 100) % 100
            key = f"{hh:02d}:{(mm//15)*15:02d}"
            buckets[key][0].append(b['q']); buckets[key][1].append((b['h'] - b['l']) / d['f'])
    for key in ['09:00', '09:15', '09:30', '09:45', '10:00', '10:15', '11:00', '13:00', '15:00', '16:45']:
        if key not in buckets:
            continue
        q, r = buckets[key]
        print(f"   {key}  contratos/min {st.mean(q):7.0f}   range médio do candle 1min {st.mean(r):5.1f} pts")
    print()

    # ---------- 3. Hindsight: 'alvo atingido' em ALGUMA direção ----------
    print("3) Em retrospecto (sem saber a direção): de 9:02 até 9:15 o preço tocou ±X?")
    for x in (0.15, 0.25, 0.35):
        up = dn = both = 0
        for d in info:
            e = d['trade'][0]['o']
            hu = max(b['h'] for b in d['trade']) >= e * (1 + x/100)
            hd = min(b['l'] for b in d['trade']) <= e * (1 - x/100)
            up += hu; dn += hd; both += hu and hd
        n = len(info)
        print(f"   ±{x:.2f}% (~{lvl*x/100:.0f} pts): subiu {up/n*100:4.0f}% | caiu {dn/n*100:4.0f}% | pelo menos um {(up+dn-both)/n*100:4.0f}% | ambos {both/n*100:4.0f}%")
    print()

    # ---------- 4. Regras definidas A PRIORI (todas reportadas) ----------
    print(f"4) Entrada 9:02, saída alvo/stop ou 9:15. Custo {COST} pts/op. Stop+alvo no mesmo candle = stop.")
    print(f"   {'regra':34s} {'alvo/stop %':>11s} {'n':>4s} {'acerto%':>7s} {'média':>7s} {'total':>7s} {'maxDD':>7s} {'t':>5s}")
    for name, sig in SINAIS.items():
        for T, S in GRADE:
            pn = [run(d, sig(d), T, S)[0] for d in info if sig(d)]
            n, wr, m, tot, dd, t = stats(pn)
            print(f"   {name:34s} {T:.2f}/{S:.2f}   {n:4d} {wr:7.1f} {m:7.1f} {tot:7.0f} {dd:7.0f} {t:5.2f}")
    print()

    # ---------- 5. Base aleatória (cara ou coroa) ----------
    random.seed(42)
    print(f"5) Direção aleatória (cara/coroa), 5.000 simulações de {len(info)} dias, alvo/stop 0,20/0,20:")
    tots = sorted(sum(run(d, random.choice((1, -1)), 0.20, 0.20)[0] for d in info) for _ in range(5000))
    print(f"   total em pts: p5 {tots[250]:.0f} | mediana {tots[2500]:.0f} | p95 {tots[4750]:.0f} | {sum(t>0 for t in tots)/50:.0f}% das simulações terminam positivas")


if __name__ == '__main__':
    main(sys.argv[1:] or [CSV_PADRAO])
