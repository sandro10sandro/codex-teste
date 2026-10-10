"""Teste FORA DA AMOSTRA da regra escolhida em abertura.py: 'Contra o gap', alvo 0,30% e stop 0,30%.

Uso:
    python3 scripts/fora_da_amostra.py WINFUT_NA_BMF_I_v6_raw.csv [outros.csv ...]

A regra foi escolhida entre 24 combinações em WINFUT_20MB_1.csv (2012-05-02 a 2012-09-20).
Esse período é reportado à parte; tudo depois dele é fora da amostra. Nada é reotimizado:
regra, alvo, stop, horário de entrada/saída e custo vêm congelados de abertura.py.

A série WIN$N não é ajustada. No dia de rolagem (quarta-feira mais próxima do dia 15 dos
meses pares, ou o pregão seguinte) o fechamento anterior é do contrato velho e a abertura é
do contrato novo, então o 'gap' é artificial: o dia fica sem operação. Dias cujo pregão
anterior está a mais de BURACO_MAX dias corridos (buraco nos dados) também ficam sem operação.
"""
import collections
import datetime as dt
import random
import statistics as st
import sys

from abertura import COST, GRADE, SINAIS, carregar, preparar, run, stats

FIM_DA_AMOSTRA = '20120920'   # último dia de WINFUT_20MB_1.csv, onde a regra foi escolhida
REGRA = 'Contra o gap'
ALVO, STOP = 0.30, 0.30
BURACO_MAX = 5                # dias corridos; acima disso o 'gap' não é overnight
REFERENCIA_AJUSTADA = "n=98 acerto=57.1% média=32.4 total=3171 maxDD=-417 t=2.94"


def data(s):
    return dt.datetime.strptime(s, '%Y%m%d').date()


def quarta_mais_proxima_do_15(ano, mes):
    d15 = dt.date(ano, mes, 15)
    desl = (2 - d15.weekday()) % 7          # 2 = quarta-feira
    return d15 + dt.timedelta(days=desl if desl <= 3 else desl - 7)


def dias_de_rolagem(dias):
    """Primeiro pregão com dados no vencimento de cada mês par (ou até 7 dias depois dele)."""
    ds = sorted(dias)
    out = set()
    for ano in range(int(ds[0][:4]), int(ds[-1][:4]) + 1):
        for mes in (2, 4, 6, 8, 10, 12):
            venc = quarta_mais_proxima_do_15(ano, mes)
            prox = next((d for d in ds if d >= venc.strftime('%Y%m%d')), None)
            if prox and (data(prox) - venc).days <= 7:
                out.add(prox)
    return out


def avaliar(sig, T, S, sub, cost=COST):
    res = [run(d, sig(d), T, S, cost) for d in sub if sig(d)]
    if not res:
        return None
    n, wr, m, tot, dd, t = stats([r[0] for r in res])
    return dict(n=n, wr=wr, m=m, tot=tot, dd=dd, t=t, saidas=collections.Counter(r[1] for r in res))


def linha(nome, r):
    if r is None:
        return f"   {nome:34s} (sem operações)"
    s = r['saidas']
    return (f"   {nome:34s} n={r['n']:4d} acerto={r['wr']:5.1f}% média={r['m']:6.1f} total={r['tot']:7.0f} "
            f"maxDD={r['dd']:6.0f} t={r['t']:5.2f}  saídas alvo/tempo/stop={s['alvo']}/{s['tempo']}/{s['stop']}")


def main(caminhos):
    days = carregar(caminhos)
    ds = list(days)
    anterior = {ds[i]: ds[i - 1] for i in range(1, len(ds))}
    info = preparar(days)
    com_info = {d['day'] for d in info}
    pulados = collections.Counter(d[:4] for d in ds if d not in com_info)
    print(f"Pregões no arquivo: {len(ds)} ({ds[0]} a {ds[-1]}). Avaliáveis (barra 9:00/9:01 e >=5 barras a partir de 9:02): {len(info)}")
    print("Pregões pulados por ano (sem barra 9:00/9:01 ou dia incompleto):", dict(sorted(pulados.items())))

    # ---------- 1. Rolagem e buracos ----------
    gap = {d: (days[d][0]['o'] / days[anterior[d]][-1]['c'] - 1) * 100 for d in ds[1:]}
    rol = dias_de_rolagem(days)
    normal = sorted(abs(g) for d, g in gap.items() if d not in rol)
    p90 = normal[int(len(normal) * 0.9)]
    print(f"\n1) Dias de rolagem (sem operação): {len(rol)}. Gap do dia (anterior | seguinte); '?' = gap abaixo do p90 dos dias normais ({p90:.2f}%)")
    cells = []
    for d in sorted(rol):
        i = ds.index(d)
        ant = gap.get(ds[i - 1], float('nan'))
        seg = gap.get(ds[i + 1], float('nan')) if i + 1 < len(ds) else float('nan')
        cells.append(f"{d} {gap.get(d, float('nan')):+5.2f}% ({ant:+.2f}|{seg:+.2f}){'?' if abs(gap.get(d, 0)) < p90 else ' '}")
    for i in range(0, len(cells), 3):
        print("   " + "   ".join(cells[i:i + 3]))
    print(f"   mediana do gap nos dias de rolagem: {st.median(gap[d] for d in rol if d in gap):+.2f}% | mediana |gap| nos demais dias: {st.median(normal):.2f}%")
    excl = collections.Counter()
    for d in info:
        if d['day'] in rol:
            d['gap'] = 0; excl['rolagem'] += 1
        elif d['day'] in anterior and (data(d['day']) - data(anterior[d['day']])).days > BURACO_MAX:
            d['gap'] = 0; excl['buraco'] += 1
    print(f"   Dias avaliáveis sem operação: rolagem {excl['rolagem']}, buraco de dados (> {BURACO_MAX} dias corridos) {excl['buraco']}")

    # ---------- 2. Dentro da amostra ----------
    sig = SINAIS[REGRA]
    nome = f"{REGRA} {ALVO:.2f}/{STOP:.2f}"
    dentro = [d for d in info if d['day'] <= FIM_DA_AMOSTRA]
    fora = [d for d in info if d['day'] > FIM_DA_AMOSTRA]
    if dentro:
        print(f"\n2) Dentro da amostra ({dentro[0]['day']} a {dentro[-1]['day']}, {len(dentro)} pregões), série bruta, custo {COST}:")
        print(linha(nome, avaliar(sig, ALVO, STOP, dentro)))
        print(f"   referência na série ajustada (abertura.py, inclui os dias de rolagem): {REFERENCIA_AJUSTADA}")
    if not fora:
        print("\nNenhum pregão fora da amostra."); return

    # ---------- 3. Fora da amostra ----------
    print(f"\n3) FORA DA AMOSTRA ({fora[0]['day']} a {fora[-1]['day']}, {len(fora)} pregões avaliáveis). Regra congelada:")
    for c in (COST, 2 * COST):
        print(linha(f"{nome} custo {c}", avaliar(sig, ALVO, STOP, fora, c)))
    lvl = st.mean(d['trade'][0]['o'] / d['f'] for d in fora)
    print(f"   nível médio do WIN no período: {lvl:,.0f} pts (0,30% ≈ {lvl * 0.003:.0f} pts)")

    # ---------- 4. Por ano ----------
    print(f"\n4) Por ano, fora da amostra, custo {COST}:")
    print(f"   {'ano':4s} {'pregões':>7s} {'n':>4s} {'acerto%':>7s} {'média':>6s} {'total':>7s} {'maxDD':>6s} {'t':>5s}  {'nível':>8s} {'0,30%':>5s}")
    anos = collections.OrderedDict()
    for d in fora:
        anos.setdefault(d['day'][:4], []).append(d)
    acum = 0; positivos = 0
    for ano, sub in anos.items():
        r = avaliar(sig, ALVO, STOP, sub)
        lv = st.mean(d['trade'][0]['o'] / d['f'] for d in sub)
        if r is None:
            print(f"   {ano} {len(sub):7d}    0"); continue
        acum += r['tot']; positivos += r['tot'] > 0
        print(f"   {ano} {len(sub):7d} {r['n']:4d} {r['wr']:7.1f} {r['m']:6.1f} {r['tot']:7.0f} {r['dd']:6.0f} {r['t']:5.2f}  {lv:8,.0f} {lv * 0.003:5.0f}")
    print(f"   anos positivos: {positivos}/{len(anos)} | total acumulado: {acum:.0f} pts")

    # ---------- 5. Resto da grade (contexto) ----------
    print(f"\n5) Fora da amostra, as outras combinações de abertura.py (NÃO pré-registradas; só contexto), custo {COST}:")
    for n_, s_ in SINAIS.items():
        for T, S in GRADE:
            print(linha(f"{n_} {T:.2f}/{S:.2f}", avaliar(s_, T, S, fora)))

    # ---------- 6. Base aleatória ----------
    random.seed(42)
    op = [d for d in fora if sig(d)]
    real = avaliar(sig, ALVO, STOP, fora)['tot']
    print(f"\n6) Base aleatória fora da amostra: direção cara/coroa nos mesmos {len(op)} dias em que a regra opera, alvo/stop {ALVO:.2f}/{STOP:.2f}, custo {COST}, 1.000 simulações:")
    tots = sorted(sum(run(d, random.choice((1, -1)), ALVO, STOP)[0] for d in op) for _ in range(1000))
    print(f"   total: p5 {tots[50]:.0f} | mediana {tots[500]:.0f} | p95 {tots[950]:.0f} | regra real {real:.0f} -> "
          f"{sum(t >= real for t in tots) / 10:.1f}% das simulações igualam ou superam a regra")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit("Informe o CSV fora da amostra, ex.: python3 scripts/fora_da_amostra.py WINFUT_NA_BMF_I_v6_raw.csv")
    main(sys.argv[1:])
