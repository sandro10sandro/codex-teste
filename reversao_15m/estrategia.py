"""Backtest do Operacional de Reversão 15 minutos (WIN).

Regra central: TOPO/FUNDO PRIMEIRO; ENGOLFO DEPOIS.
Ver reversao_15m/REGRAS.md para a especificação completa e a quantificação
de cada critério.
"""

from pathlib import Path

import pandas as pd

CSV = Path(__file__).resolve().parent.parent / "WINFUT_20MB_1.csv"
SAIDA_TRADES = Path(__file__).resolve().parent / "trades.csv"
SAIDA_VETOS = Path(__file__).resolve().parent / "sinais_vetados.csv"

# Gestão fixa (em pontos)
STOP_LOSS = 360.0
TAKE_PROFIT = 650.0

# Região de topo/fundo: extremo dos últimos N candles de 15 min
LOOKBACK_EXTREMO = 20

# Segunda oportunidade: engolfo na mesma região, em até K candles do sinal
# original, desde que o preço não tenha andado DESLOCAMENTO_MAX ou mais
JANELA_SEGUNDA_CHANCE = 8
DESLOCAMENTO_MAX = 500.0


def carregar_1min(caminho: Path) -> pd.DataFrame:
    df = pd.read_csv(caminho)
    df.columns = [c.strip("<>") for c in df.columns]
    ts = pd.to_datetime(
        df["date"].astype(str) + df["time"].astype(str).str.zfill(6),
        format="%Y%m%d%H%M%S",
    )
    df = df.assign(ts=ts).sort_values("ts").set_index("ts")
    return df[["open", "high", "low", "close"]]


def agregar_15min(m1: pd.DataFrame) -> pd.DataFrame:
    m15 = m1.resample("15min").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
    )
    return m15.dropna()


def engolfo(prev: pd.Series, cur: pd.Series) -> str | None:
    """Retorna 'baixa', 'alta' ou None. Engolfo de corpo, corpos não nulos."""
    if prev["close"] > prev["open"] and cur["close"] < cur["open"]:
        if cur["open"] >= prev["close"] and cur["close"] <= prev["open"]:
            return "baixa"
    if prev["close"] < prev["open"] and cur["close"] > cur["open"]:
        if cur["open"] <= prev["close"] and cur["close"] >= prev["open"]:
            return "alta"
    return None


def simular_saida(m1: pd.DataFrame, inicio, dia, lado: str, entrada: float):
    """Percorre os candles de 1 min do dia a partir de `inicio` aplicando
    SL/TP fixos. Se SL e TP couberem no mesmo candle, assume o pior caso (SL).
    Sem saída até o fim do dia, zera no fechamento do último candle."""
    if lado == "venda":
        alvo, stop = entrada - TAKE_PROFIT, entrada + STOP_LOSS
    else:
        alvo, stop = entrada + TAKE_PROFIT, entrada - STOP_LOSS

    janela = m1.loc[(m1.index >= inicio) & (m1.index.date == dia)]
    for ts, barra in janela.iterrows():
        if lado == "venda":
            if barra["high"] >= stop:
                return ts, stop, "stop"
            if barra["low"] <= alvo:
                return ts, alvo, "alvo"
        else:
            if barra["low"] <= stop:
                return ts, stop, "stop"
            if barra["high"] >= alvo:
                return ts, alvo, "alvo"
    ultimo = janela.iloc[-1]
    return janela.index[-1], ultimo["close"], "fim_do_dia"


def rodar() -> tuple[pd.DataFrame, pd.DataFrame]:
    m1 = carregar_1min(CSV)
    m15 = agregar_15min(m1)
    m15["dia"] = m15.index.date
    maxima_n = m15["high"].rolling(LOOKBACK_EXTREMO, min_periods=1).max()
    minima_n = m15["low"].rolling(LOOKBACK_EXTREMO, min_periods=1).min()

    trades, vetos = [], []
    posicao_ate = None  # timestamp até o qual há posição aberta
    # última região válida por direção: {'baixa': (idx_barra, extremo), ...}
    regioes: dict[str, tuple[int, float]] = {}

    for i in range(1, len(m15)):
        prev, cur = m15.iloc[i - 1], m15.iloc[i]
        if prev["dia"] != cur["dia"]:
            continue
        lado_engolfo = engolfo(prev, cur)
        if lado_engolfo is None:
            continue

        ts_candle = m15.index[i]
        # Contexto: o par de candles do engolfo marca o extremo dos últimos N?
        if lado_engolfo == "baixa":
            em_extremo = max(cur["high"], prev["high"]) >= maxima_n.iloc[i]
            extremo = max(cur["high"], prev["high"])
        else:
            em_extremo = min(cur["low"], prev["low"]) <= minima_n.iloc[i]
            extremo = min(cur["low"], prev["low"])

        segunda_chance = False
        if em_extremo:
            regioes[lado_engolfo] = (i, extremo)
        else:
            regiao = regioes.get(lado_engolfo)
            if (
                regiao is not None
                and i - regiao[0] <= JANELA_SEGUNDA_CHANCE
                and abs(cur["close"] - regiao[1]) < DESLOCAMENTO_MAX
            ):
                segunda_chance = True
            else:
                vetos.append(
                    {
                        "candle_15m": ts_candle,
                        "engolfo": lado_engolfo,
                        "fechamento": cur["close"],
                        "motivo": (
                            "sem_regiao" if regiao is None else "deslocado_ou_tarde"
                        ),
                    }
                )
                continue

        # Entrada a mercado após o fechamento do candle de 15 min
        fim_candle = ts_candle + pd.Timedelta(minutes=15)
        pos_1m = m1.loc[(m1.index >= fim_candle) & (m1.index.date == cur["dia"])]
        if pos_1m.empty:
            continue  # engolfo no último candle do dia: sem barra para entrar
        ts_entrada = pos_1m.index[0]
        if posicao_ate is not None and ts_entrada < posicao_ate:
            continue  # já posicionado; a região segue válida p/ 2ª oportunidade

        lado = "venda" if lado_engolfo == "baixa" else "compra"
        entrada = pos_1m.iloc[0]["open"]
        ts_saida, preco_saida, motivo = simular_saida(
            m1, ts_entrada, cur["dia"], lado, entrada
        )
        posicao_ate = ts_saida
        pontos = entrada - preco_saida if lado == "venda" else preco_saida - entrada
        trades.append(
            {
                "candle_sinal": ts_candle,
                "lado": lado,
                "segunda_chance": segunda_chance,
                "entrada_ts": ts_entrada,
                "entrada": round(entrada, 2),
                "saida_ts": ts_saida,
                "saida": round(preco_saida, 2),
                "motivo_saida": motivo,
                "pontos": round(pontos, 2),
            }
        )

    return pd.DataFrame(trades), pd.DataFrame(vetos)


def resumo(trades: pd.DataFrame, vetos: pd.DataFrame) -> str:
    if trades.empty:
        return "Nenhum trade gerado."
    ganhos = trades[trades["pontos"] > 0]
    linhas = [
        f"Trades: {len(trades)}  (compras: {(trades['lado'] == 'compra').sum()}, "
        f"vendas: {(trades['lado'] == 'venda').sum()}, "
        f"segunda oportunidade: {trades['segunda_chance'].sum()})",
        f"Sinais vetados (engolfo fora de topo/fundo): {len(vetos)}",
        f"Taxa de acerto: {len(ganhos) / len(trades):.1%}",
        f"Resultado total: {trades['pontos'].sum():+.0f} pontos",
        f"Média por trade: {trades['pontos'].mean():+.1f} pontos",
        "Saídas: "
        + ", ".join(
            f"{motivo}={qtd}" for motivo, qtd in trades["motivo_saida"].value_counts().items()
        ),
    ]
    return "\n".join(linhas)


if __name__ == "__main__":
    trades, vetos = rodar()
    trades.to_csv(SAIDA_TRADES, index=False)
    vetos.to_csv(SAIDA_VETOS, index=False)
    print(resumo(trades, vetos))
    print(f"\nDetalhes em {SAIDA_TRADES.name} e {SAIDA_VETOS.name}")
