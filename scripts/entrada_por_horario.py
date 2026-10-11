"""Testa o 'operacional de 15 minutos' com entrada em VÁRIOS horários: lê de 9:00 até o minuto
anterior à entrada, entra na abertura do candle do horário e sai no alvo, no stop ou 15 minutos
depois (fechamento do 15º candle).

Uso:
    python3 scripts/entrada_por_horario.py WINFUT_NA_BMF_I_v6_raw.csv            # horários padrão
    python3 scripts/entrada_por_horario.py WINFUT_NA_BMF_I_v6_raw.csv 09:05 09:20

Para cada horário de entrada E, regras fixadas antes de rodar (as mesmas de entrada_0915.py):
  - leitura = candles de 9:00 a E-1 min; o dia só vale se o primeiro candle lido é até
    max(9:00, E-5 min) e há pelo menos 2/3 dos minutos (mín. 2);
  - sinais: momentum (fechamento de E-1 vs abertura do 1º candle lido), reversão, segue o gap,
    contra o gap, sempre comprado, sempre vendido; grade de alvo/stop de abertura.py; custo 10;
  - entrada na abertura do candle E (exigido), saída até o fechamento de E+14 (>= 10 candles);
  - rompimento da faixa lida: stop no outro extremo, alvo 1x a faixa, até E+44 min.
Com E = 09:15 isto reproduz exatamente entrada_0915.py (serve de teste de regressão).
Na série WIN$N os dias de rolagem e os dias após buraco ficam sem operação nos sinais de gap.
São dezenas de combinações por horário: com 8 horários e 25 regras, espera-se que meia dúzia
pareça boa por acaso. Só vale olhar o que é positivo nas duas metades, e mesmo isso é hipótese.
"""
import collections
import statistics as st
import sys

from abertura import COST, GRADE, carregar, factor, sinal
from entrada_0915 import avaliar_rompimento, resumo
from fora_da_amostra import BURACO_MAX, avaliar, data, dias_de_rolagem, linha

HORARIOS_PADRAO = ['09:02', '09:05', '09:07', '09:08', '09:10', '09:12', '09:15', '09:20']

SINAIS = {   # mesmos sinais de entrada_0915.py, lidos de 9:00 até o minuto anterior à entrada
    'Momentum desde 9:00':  lambda d: d['mom'],
    'Reversão desde 9:00':  lambda d: -d['mom'],
    'Segue o gap':          lambda d: d['gap'],
    'Contra o gap':         lambda d: -d['gap'],
    'Sempre comprado':      lambda d: 1,
    'Sempre vendido':       lambda d: -1,
}
DURACAO = 15          # minutos em posição (candle de entrada incluído)
ROMPIMENTO_ATE = 45   # minutos para a regra de rompimento


def minutos(t):
    return t // 10000 * 60 + (t // 100) % 100


def hhmmss(m):
    return (m // 60) * 10000 + (m % 60) * 100


def hm(m):
    return f"{m // 60:02d}:{m % 60:02d}"


def preparar(days, entrada):
    e = minutos(entrada)
    ini = minutos(90000)
    min_leitura = max(2, (e - ini) * 2 // 3)
    primeiro_max = max(ini, e - 5)
    fim_trade, fim_depois = e + DURACAO - 1, e + ROMPIMENTO_ATE - 1
    keys = list(days)
    info = []
    for i, k in enumerate(keys):
        bars = days[k]
        leitura = [b for b in bars if ini <= minutos(b['t']) < e]
        trade = [b for b in bars if e <= minutos(b['t']) <= fim_trade]
        depois = [b for b in bars if e <= minutos(b['t']) <= fim_depois]
        if (len(leitura) < min_leitura or minutos(leitura[0]['t']) > primeiro_max
                or len(trade) < 10 or minutos(trade[0]['t']) != e):
            continue
        prev_close = days[keys[i - 1]][-1]['c'] if i > 0 else None
        info.append(dict(day=k, f=factor(bars), win=leitura, trade=trade, depois=depois,
                         hi=max(b['h'] for b in leitura), lo=min(b['l'] for b in leitura),
                         mom=sinal(leitura[-1]['c'] - leitura[0]['o']),
                         gap=sinal(leitura[0]['o'] - prev_close) if prev_close else 0))
    return info


def excluir_gap_artificial(info, days, rol):
    ds = list(days)
    anterior = {ds[i]: ds[i - 1] for i in range(1, len(ds))}
    n = 0
    for d in info:
        if d['day'] in rol or (d['day'] in anterior and (data(d['day']) - data(anterior[d['day']])).days > BURACO_MAX):
            d['gap'] = 0; n += 1
    return n


def main(caminho, horarios):
    days = carregar([caminho])
    rol = dias_de_rolagem(days)
    resumo_final = []
    for hor in horarios:
        entrada = int(hor.replace(':', '')) * 100
        info = preparar(days, entrada)
        if not info:
            print(f"\n=== Entrada {hor}: nenhum dia avaliável ===")
            continue
        n_excl = excluir_gap_artificial(info, days, rol)
        h = len(info) // 2
        m1, m2 = info[:h], info[h:]
        e = minutos(entrada)
        print(f"\n=== Entrada {hor} (leitura 09:00-{hm(e - 1)}, saída até o fechamento de {hm(e + DURACAO - 1)}, "
              f"rompimento até {hm(e + ROMPIMENTO_ATE - 1)}) ===")
        print(f"Avaliáveis: {len(info)} de {len(days)} pregões | 1ª metade {m1[0]['day']} a {m1[-1]['day']} | "
              f"2ª metade {m2[0]['day']} a {m2[-1]['day']} | sem gap por rolagem/buraco: {n_excl}")
        amp = st.median((max(b['h'] for b in d['trade']) - min(b['l'] for b in d['trade'])) / d['f'] for d in info)
        lvl = st.mean(d['trade'][0]['o'] / d['f'] for d in info)
        print(f"Amplitude mediana da janela operada: {amp:.0f} pts; 0,30% ≈ {lvl * 0.003:.0f} pts")
        print(f"   {'regra':34s} {'alvo/stop':>9s}  {'todo':^30s} | {'1ª metade':^30s} | {'2ª metade':^30s}")
        melhor = None
        for nome, sig in SINAIS.items():
            for T, S in GRADE:
                r, r1, r2 = (avaliar(sig, T, S, sub) for sub in (info, m1, m2))
                print(f"   {nome:34s} {T:.2f}/{S:.2f}  {resumo(r)} | {resumo(r1)} | {resumo(r2)}")
                if r and (melhor is None or r['t'] > melhor[1]['t']):
                    melhor = (f"{nome} {T:.2f}/{S:.2f}", r, r1, r2)
        print("   sem custo, 0,30/0,30:")
        bruto = {}
        for nome, sig in SINAIS.items():
            if nome.startswith(('Momentum', 'Segue', 'Sempre comprado')):
                r, r1, r2 = (avaliar(sig, 0.30, 0.30, sub, 0) for sub in (info, m1, m2))
                bruto[nome.split(' ')[0]] = r
                print(f"   {nome:34s}            {resumo(r)} | {resumo(r1)} | {resumo(r2)}")
        rb, rb1, rb2 = (avaliar_rompimento(sub) for sub in (info, m1, m2))
        print(linha("Rompimento da faixa lida (todo)", rb) if rb else "   Rompimento: sem operações")
        print(f"   {'Rompimento, metades':34s}            {resumo(rb1)} | {resumo(rb2)}")
        resumo_final.append((hor, len(info), melhor, bruto.get('Momentum'), rb))

    print("\n=== RESUMO POR HORÁRIO (custo 10, salvo onde indicado) ===")
    print(f"   {'entrada':7s} {'dias':>5s}  {'melhor regra da grade (por t)':44s} {'média':>6s} {'t':>5s} {'1ª met.':>7s} {'2ª met.':>7s} | "
          f"{'momentum s/ custo':>17s} | {'rompimento':>10s}")
    for hor, n, melhor, mom0, rb in resumo_final:
        nome, r, r1, r2 = melhor
        print(f"   {hor:7s} {n:5d}  {nome:44s} {r['m']:6.1f} {r['t']:5.2f} {r1['m']:7.1f} {r2['m']:7.1f} | "
              f"{mom0['m']:+6.1f} (t {mom0['t']:4.2f}) | {rb['m']:6.1f} (t {rb['t']:5.2f})")
    print("   Com 25 regras por horário, uma regra com t ≈ 2 num só período é esperada por acaso.")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit("Informe o CSV, ex.: python3 scripts/entrada_por_horario.py WINFUT_NA_BMF_I_v6_raw.csv 09:05 09:20")
    main(sys.argv[1], sys.argv[2:] or HORARIOS_PADRAO)
