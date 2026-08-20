# Operacional de Reversão — 15 minutos (WIN)

Regra central: **TOPO/FUNDO PRIMEIRO; ENGOLFO DEPOIS.**
O engolfo confirma a entrada, mas quem autoriza o setup é a localização.

## Regras operacionais

1. **Contexto obrigatório**: a operação só pode acontecer depois que o preço
   chegar a uma região clara de topo ou fundo. O engolfo é apenas o gatilho;
   não é suficiente sozinho.
2. **Venda no topo**: o preço sobe, alcança/formaliza uma região de topo e
   surge um engolfo de baixa. Assim que o candle do engolfo **fechar**, entrar
   vendido a mercado (sem antecipar durante a formação do candle).
3. **Compra no fundo**: o preço cai, alcança/formaliza uma região de fundo e
   surge um engolfo de alta. Assim que o candle do engolfo **fechar**, entrar
   comprado a mercado.
4. **Gestão fixa**: Stop Loss de **360 pontos** e Take Profit de **650 pontos**.
5. **Segunda oportunidade**: se a primeira entrada não for feita, é permitido
   entrar no segundo candle de engolfo na mesma região, desde que o preço ainda
   não tenha se deslocado demais. Se já tiver andado **aproximadamente 500
   pontos ou mais** a partir da região do sinal, não entrar.
6. **Veto principal**: não operar engolfo que apareça no meio do caminho.
   Exemplo: o mercado cai, forma um fundo, sobe sem engolfo e, durante essa
   subida, aparece um engolfo de baixa — não vende, porque o engolfo não surgiu
   em um topo válido.

## Quantificação usada no backtest (`estrategia.py`)

A regra discricionária fala em "região clara de topo/fundo"; para tornar o
backtest reprodutível, os critérios foram quantificados assim (todos são
parâmetros ajustáveis no topo do script):

| Conceito | Implementação | Parâmetro |
|---|---|---|
| Engolfo de baixa | Candle anterior de alta, candle atual de baixa, e o **corpo** atual engolfa o corpo anterior (abertura ≥ fechamento anterior e fechamento ≤ abertura anterior). Corpos não nulos. | — |
| Engolfo de alta | Simétrico ao de baixa. | — |
| Região de topo | A máxima do par (candle do engolfo + candle anterior) é a **maior máxima dos últimos N candles de 15 min**. | `LOOKBACK_EXTREMO = 20` |
| Região de fundo | Simétrico: menor mínima dos últimos N candles. | `LOOKBACK_EXTREMO = 20` |
| Segunda oportunidade | Engolfo na mesma direção de uma região válida recente (últimos `JANELA_SEGUNDA_CHANCE` candles), aceito só se o fechamento do engolfo estiver a **menos de 500 pontos** do extremo da região. | `JANELA_SEGUNDA_CHANCE = 8`, `DESLOCAMENTO_MAX = 500` |
| Veto "meio do caminho" | Engolfo que não está em extremo de N candles **e** não se qualifica como segunda oportunidade é descartado. | — |
| Entrada | A mercado no **open do primeiro candle de 1 min após o fechamento** do candle de engolfo de 15 min. | — |
| Saída | SL 360 / TP 650, verificados candle a candle **no gráfico de 1 minuto** (se SL e TP couberem no mesmo candle de 1 min, assume-se o pior caso: stop). | `STOP_LOSS = 360`, `TAKE_PROFIT = 650` |
| Day trade | Posição aberta é zerada no fechamento do último candle de 1 min do dia. | — |
| Posição | Uma posição por vez; sinais durante posição aberta são ignorados (mas a região continua válida para a segunda oportunidade). | — |

## Como rodar

```bash
pip install pandas
python3 reversao_15m/estrategia.py
```

Saídas: resumo no terminal, trades em `reversao_15m/trades.csv` e sinais
vetados em `reversao_15m/sinais_vetados.csv`.
