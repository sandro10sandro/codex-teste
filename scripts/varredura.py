"""Varredura ampla: para muitos horários de entrada e tempos em posição, roda todas as regras da
grade e o rompimento, e reporta se ALGUMA combinação tem edge — definido como média positiva
líquida de custo (10 pts) no período inteiro E nas duas metades, com t >= 1,0 nas duas.

Uso:
    python3 scripts/varredura.py WINFUT_NA_BMF_I_v6_raw.csv

É uma busca em centenas de combinações; o critério das duas metades é o filtro contra achados de
sorte. Nada que passe aqui é garantia: seria só uma hipótese para teste fora da amostra futuro.
"""
import sys

import entrada_por_horario as EH
from abertura import GRADE
from entrada_por_horario import SINAIS, avaliar_rompimento, excluir_gap_artificial, minutos, preparar
from fora_da_amostra import avaliar, dias_de_rolagem

HORARIOS = ['09:30', '10:00', '10:30', '11:00', '11:30', '12:00', '13:00', '14:00', '15:00']
DURACOES = [15, 30, 60]
CUSTO = 10
T_MIN = 1.0   # t mínimo exigido em cada metade para marcar como candidato


def metades(info):
    h = len(info) // 2
    return info, info[:h], info[h:]


def candidato(r, r1, r2):
    return (r and r1 and r2 and r['m'] > 0 and r1['m'] > 0 and r2['m'] > 0
            and r1['t'] >= T_MIN and r2['t'] >= T_MIN)


def main(caminho):
    days = EH.carregar([caminho])
    rol = dias_de_rolagem(days)
    candidatos = []
    print(f"Varredura: {len(HORARIOS)} horários x {len(DURACOES)} durações x (24 regras + rompimento), custo {CUSTO}.")
    print(f"Edge = média > 0 no período todo e nas duas metades, com t >= {T_MIN} nas duas.\n")
    print(f"   {'entrada':7s} {'dur':>3s} {'dias':>5s}  {'melhor regra (por menor t das 2 metades)':44s} {'todo':>6s} {'t1':>5s} {'t2':>5s}")
    for dur in DURACOES:
        for hor in HORARIOS:
            EH.DURACAO = dur
            EH.ROMPIMENTO_ATE = dur + 30
            info = preparar(days, int(hor.replace(':', '')) * 100)
            if not info:
                print(f"   {hor:7s} {dur:3d}     0  (nenhum dia avaliável)"); continue
            excluir_gap_artificial(info, days, rol)
            todo, m1, m2 = metades(info)
            melhor = None
            for nome, sig in SINAIS.items():
                for T, S in GRADE:
                    r, r1, r2 = (avaliar(sig, T, S, sub, CUSTO) for sub in (todo, m1, m2))
                    if r is None:
                        continue
                    score = min(r1['t'], r2['t'])
                    if melhor is None or score > melhor[0]:
                        melhor = (score, f"{nome} {T:.2f}/{S:.2f}", r, r1, r2)
                    if candidato(r, r1, r2):
                        candidatos.append((hor, dur, f"{nome} {T:.2f}/{S:.2f}", r, r1, r2))
            rb, rb1, rb2 = (avaliar_rompimento(sub, CUSTO) for sub in (todo, m1, m2))
            if candidato(rb, rb1, rb2):
                candidatos.append((hor, dur, "Rompimento", rb, rb1, rb2))
            _, nome, r, r1, r2 = melhor
            print(f"   {hor:7s} {dur:3d} {len(info):5d}  {nome:44s} {r['m']:6.1f} {r1['t']:5.2f} {r2['t']:5.2f}")
        print()

    print("=" * 80)
    if candidatos:
        print(f"CANDIDATOS COM EDGE ({len(candidatos)}): média > 0 e t >= {T_MIN} nas duas metades")
        for hor, dur, nome, r, r1, r2 in candidatos:
            print(f"   entrada {hor} dur {dur}: {nome} | todo média {r['m']:+.1f} t {r['t']:.2f} | "
                  f"1ª {r1['m']:+.1f} t {r1['t']:.2f} | 2ª {r2['m']:+.1f} t {r2['t']:.2f}")
    else:
        print("NENHUM CANDIDATO COM EDGE. Nenhuma combinação (horário x duração x regra) ficou positiva")
        print("líquida de custo nas duas metades. Confirma que não há operacional de abertura/manhã")
        print("com vantagem nesse conjunto de regras e dados.")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit("Informe o CSV.")
    main(sys.argv[1])
