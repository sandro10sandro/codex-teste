# Handoff — Teste do "operacional de 15 minutos" na abertura do WINFUT

Este arquivo passa para outra sessão (ou outra pessoa) **tudo que já foi analisado** e
**tudo que ainda falta analisar** sobre a ideia de operar só a janela das 9:00 às 9:15 do
mini índice (WIN). Ele é autossuficiente: dá para ler só este arquivo e continuar o trabalho.

---

## 0. Prompt pronto para colar numa nova sessão

> Continue a análise descrita em `HANDOFF.md` deste repositório. A regra "contra o gap" com
> alvo/stop de 0,30%, escolhida em 99 pregões de 2012 (`scripts/abertura.py`), **já foi testada
> fora da amostra** em 2012-09 a 2026-08 (`scripts/fora_da_amostra.py`, saída em
> `resultados/fora_da_amostra_2012-2026.txt`) e **não tem edge**: -6,9 pts por operação com custo
> de 10 pts e +3,1 sem custo (t = 0,83). Não reotimize nem procure outra regra nos mesmos dados.
> O que ainda vale fazer está na seção 6: entender o novo regime de abertura do WIN (desde
> out/nov de 2025 metade dos pregões não tem candle de 9:00) e, se for seguir, só com hipótese
> nova fixada antes e dados posteriores a 2026-09. A entrada às 9:15 também já foi testada
> (`scripts/entrada_0915.py`): tudo negativo.

---

## 1. Contexto e objetivo

A pergunta original: **é possível ter um operacional de ~15 minutos na abertura do WIN**, como
o que circula em imagem de rede social (entra 9:02 com plano, alvo batido 9:12, "dia resolvido
em 15 minutos")?

A abordagem aqui foi: definir regras **antes** de ver os resultados (sem viés de análises
anteriores), testar todas, reportar inclusive as que perderam, e medir se sobra algo depois de
custos e de checagens de robustez.

**Resposta curta:** não, não do jeito da imagem. A única regra que parecia funcionar em 2012
(contra o gap, alvo e stop de 0,30%) foi testada em 14 anos de dados que não entraram na escolha e
não tem edge: perde 6,9 pts por operação com custo de 10 pts e rende 3,1 pts por operação sem
custo nenhum, o que é indistinguível de zero. As 24 combinações testadas são todas negativas fora
da amostra. Além disso, desde outubro/novembro de 2025 o pregão do WIN em cerca de metade dos
dias só começa às 9:02 ou 9:03 (print de leilão), então "ler 9:00-9:02 e entrar às 9:02" nem é
executável como descrito.

---

## 2. Dados usados

- Arquivo: `WINFUT_20MB_1.csv` (está na raiz do repositório).
- Ticker: `WIN$D` (série contínua ajustada).
- Granularidade: candles de 1 minuto.
- Período: **99 pregões, 2012-05-02 a 2012-09-20**. 50.000 linhas de dados.
- O arquivo termina cortado às 09:34 de 2012-09-20 → parece ser a **parte 1** de uma
  exportação fatiada do Profit. Por isso os scripts juntam vários arquivos (ver seção 8).
- Todos os candles são do pregão normal (`<aft> = N`); não há after-market no arquivo.
- Formato das colunas (exportação do Profit):
  `<ticker>,<date>,<time>,<trades>,<close>,<low>,<high>,<open>,<vol>,<qty>,<aft>`

**Detalhe importante do dado:** a série WIN$D é **ajustada multiplicativamente** (não bate com o
preço nominal do dia). Os scripts recuperam os pontos reais pelo tamanho do tick: o menor passo
de preço de cada dia equivale a 1 tick = 5 pontos. Todos os resultados em "pts" abaixo já estão
nessa escala de pontos reais.

**Arquivo 2 (fora da amostra):** `WINFUT_NA_BMF_I_v6_raw.csv`.

- 154 MB, **não está no repositório** (acima do limite do GitHub). Chegou em duas partes
  `WINFUT_NA_BMF_I_v6_raw.rar.001/.002` (RAR 5 cortado por byte: `cat *.001 *.002 > x.rar` e
  `unrar x x.rar`). O sha256 do CSV está no cabeçalho de `resultados/fora_da_amostra_2012-2026.txt`.
- Ticker `WIN$N` (série contínua **não ajustada**, preços em pontos reais), candles de 1 minuto,
  **3.533 pregões, 2012-05-02 a 2026-09-02**, 1.915.016 linhas, sem after-market, sem duplicatas,
  tick de 5 pts em todos os dias, nenhum candle inválido (verificado).
- Defeitos conhecidos: dois buracos de 12 pregões (2016-12-14 a 2016-12-29 e 2017-06-14 a
  2017-06-30); campo `<trades>` zerado entre 2025-04-22 e 2025-07-11 (preços e volume normais);
  395 pregões sem candle de 9:00/9:01 (14 Quartas-feiras de Cinzas, 3 dias parciais e ~378 dias em
  que o primeiro candle, às 9:02-9:10, é o print de um leilão de abertura prolongado; concentrados
  em 2016, 2018, 2020, 2025 e 2026). Esses dias ficam fora do teste, que exige o candle de 9:00.
- Rolagem: a série troca de contrato na abertura da quarta-feira mais próxima do dia 15 dos meses
  pares (confirmado contra a série ajustada em 2012-06-13 e 2012-08-15; os gaps desses dias têm
  mediana +1,47% contra 0,33% nos demais). `fora_da_amostra.py` deixa esses dias sem operação.

---

## 3. Metodologia e premissas

- **Entrada:** na abertura do candle de 9:02 (depois de "ler" os 2 primeiros minutos 9:00–9:01).
- **Saída:** no alvo, no stop, ou no fechamento de 9:14 (= início de 9:15), o que vier primeiro.
- **Custo:** 10 pts por operação (ida+volta) no teste principal; 20 pts no teste de robustez.
  Isso cobre ~1 tick de slippage na entrada e ~1 na saída; taxas são desprezíveis em pontos.
- **Candle de 1 min não diz a ordem dos preços dentro do candle.** Quando stop e alvo caem no
  mesmo candle, conta-se como **stop** (conservador).
- **Regras e alvos/stops foram fixados A PRIORI** e todas são reportadas, inclusive as perdedoras.
- Estatística `t` = t-Student da média por operação (quão longe de zero está o retorno médio).
- **Na série não ajustada** (WIN$N), dias de rolagem e dias cujo pregão anterior está a mais de
  5 dias corridos ficam sem operação, porque o gap não é overnight. Só `fora_da_amostra.py` faz isso.

---

## 4. O que já foi analisado (resultados sobre WINFUT_20MB_1.csv)

### 4.1 Características da janela 9:00–9:15
- Amplitude 9:00–9:15: **mediana 265 pts** (~0,46%) | média 302 | p10 155 | p90 450.
- Amplitude do dia inteiro: mediana 1250 pts → a janela é **~21% do range diário**.
- Deslocamento líquido 9:02→9:15: mediana **75 pts** (o preço anda, mas volta bastante).
- Nível médio do WIN no período: ~57.019 pts (então 0,25% ≈ 143 pts).

### 4.2 Volume e volatilidade por horário (média por minuto)
| Faixa | Contratos/min | Range médio do candle 1min |
|------|---------------|----------------------------|
| 09:00 | 217 | 66 pts |
| 09:15 | 212 | 51 pts |
| 09:30 | 293 | 64 pts |
| 10:00 | 443 | 65 pts |
| 11:00 | 641 | 75 pts |
| 13:00 | 239 | 41 pts |

Leitura: em 2012 a abertura (9h) tinha **~metade do volume das 10h** (o à vista abre 10h).
Liquidez suficiente para pessoa física, mas não é o pico do dia.

### 4.3 "Alvo atingido" em retrospecto (sem saber a direção)
De 9:02 a 9:15, com que frequência o preço tocou ±X para **algum** lado:
| Alvo | Subiu | Caiu | Pelo menos um | Ambos |
|------|-------|------|---------------|-------|
| ±0,15% (~86 pts) | 57% | 48% | **89%** | 16% |
| ±0,25% (~143 pts) | 31% | 25% | **55%** | 2% |
| ±0,35% (~200 pts) | 17% | 13% | **29%** | 1% |

É a "ilusão do retrovisor": quase todo dia dá para tirar um print de "alvo atingido". O difícil
é **acertar a direção** às 9:02.

### 4.4 Regras testadas (entrada 9:02, custo 10 pts)
Melhores e piores combinações (média = pts por operação; t = significância):

| Regra | Alvo/Stop | n | Acerto | Média | Total | maxDD | t |
|-------|-----------|---|--------|-------|-------|-------|---|
| **Contra o gap** | 0,30/0,30 | 98 | 57,1% | **+32,4** | +3171 | -417 | **2,94** |
| Contra o gap | 0,15/0,30 | 98 | 65,3% | +20,0 | +1956 | -345 | 2,53 |
| Contra o gap | 0,20/0,20 | 98 | 59,2% | +16,9 | +1658 | -579 | 1,75 |
| Momentum 2min | 0,20/0,20 | 95 | 58,9% | +16,2 | +1537 | -402 | 1,63 |
| Sempre comprado | 0,20/0,20 | 99 | 50,5% | -4,4 | -438 | -1421 | -0,44 |
| Reversão 2min | 0,20/0,20 | 95 | 36,8% | -36,2 | -3437 | -3437 | -3,64 |
| Segue o gap | 0,20/0,20 | 98 | 35,7% | -36,9 | -3618 | -3927 | -3,81 |

- **Contra o gap** (vende se abriu acima do fechamento anterior, compra se abriu abaixo) foi a
  única consistentemente positiva, nos quatro pares de alvo/stop.
- **Seguir o gap**, **reversão do momentum** e **sempre vendido** deram prejuízo claro.
- **Momentum 2min** (seguir a direção de 9:00→9:02) ficou positivo mas instável (ver 4.6).

### 4.5 Base aleatória (cara ou coroa)
Direção escolhida no cara/coroa, alvo/stop 0,20/0,20, 5.000 simulações de 99 dias:
total em pts — p5 **-2675** | mediana **-1010** | p95 **+613**. Só **15%** terminam positivas.
Ou seja: entrar sem edge perde por causa do custo. Qualquer regra tem que bater isso.

### 4.6 Robustez (a parte que mais importa)
- **Metades do período** (contra o gap):
  - 1ª metade (mai–jul): 0,30/0,30 média +41,8 (t=2,51); 0,20/0,20 média +40,0 (t=3,17).
  - 2ª metade (jul–set): 0,30/0,30 média +23,3 (t=1,63); **0,20/0,20 média -5,2 (t=-0,37)**.
  - → a versão 0,20/0,20 **quebra** na 2ª metade; a 0,30/0,30 cai mas continua positiva.
- **Custo dobrado (20 pts/op):** contra o gap 0,30/0,30 ainda **+22,4** média (t=2,03);
  a 0,20/0,20 despenca para +6,9 (t=0,72). → **a 0,30/0,30 é a mais robusta.**
- **Sem os 5 melhores dias:** contra o gap 0,30/0,30 ainda soma +2311 de +3171 (não depende de
  um punhado de dias isolados).
- **Tamanho do gap:** gaps grandes (metade superior) rendem média +42,2 (t=2,98); gaps pequenos
  +22,5 (t=1,35). → o edge vem **principalmente dos dias de gap grande**.
- **Saídas da regra 0,30/0,30:** 31 por alvo, 59 por tempo (9:15), 8 por stop. Ou seja, a maioria
  dos dias **sai zerando no horário**, não batendo o alvo — nada de "dia resolvido 9:12".

### 4.7 Fora da amostra: 2012-09-21 a 2026-08-25 (`scripts/fora_da_amostra.py`)
Regra congelada ("contra o gap", 0,30/0,30, entrada 9:02, saída no alvo, no stop ou às 9:15),
sem nenhuma reotimização, no arquivo WIN$N. Dentro da amostra (2012-05-02 a 2012-09-20) o
arquivo bruto reproduz a série ajustada (n=96, 57,3%, +31,8/op, t 2,86; a diferença são 2 dias
de rolagem sem operação), o que valida o pipeline.

| Período | n | Acerto | Média/op | Total | maxDD | t |
|---|---|---|---|---|---|---|
| Fora da amostra, custo 10 | 2921 | 47,4% | **-6,9** | -20.185 | -24.592 | **-1,85** |
| Fora da amostra, custo 20 | 2921 | 45,0% | -16,9 | -49.395 | -50.600 | -4,52 |
| Fora da amostra, custo 0 | 2921 | 49,8% | +3,1 | +9.025 | — | 0,83 |

- Saídas: 529 por alvo (18%), 1.867 por tempo, 525 por stop.
- Por ano: 5 positivos em 15 (2012, 2019, 2022, 2024, 2025); piores 2020 (-26/op) e 2026
  (-28,6/op). O trecho 2022-2025 positivo é seleção a posteriori: 4ª melhor de 120 janelas de
  anos contíguos, e o acaso produz isso em 26% dos sorteios.
- As outras 23 combinações da grade também são negativas fora da amostra com custo 10.
- Base aleatória nos mesmos 2.921 dias (1.000 sorteios de direção): mediana -29.808; a regra fica
  no percentil 80, que é só outra forma de dizer t = 0,83 do ganho bruto.
- Gaps grandes, que em 2012 pareciam a fonte do edge, são o **pior quartil** fora da amostra
  (|gap| ≥ 0,5%: -18,6/op, t -2,58).
- Nenhuma variante salva: alvo em pontos fixos, em %, normalizado por volatilidade ou múltiplo do
  gap; sem alvo/stop; segurar até 9:29, 9:59 ou 10:29; walk-forward entre as 24 combinações
  (-12,7/op, t -3,84); incluir os dias sem candle de 9:00 com entrada no 1º candle disponível.
- Verificação independente (sessão de 2026-10-10): reimplementação do zero a partir da
  especificação reproduziu todos os números (n, totais por ano, saídas); auditoria de código sem
  lookahead; varredura dos dados sem candle inválido; cético e crítico não encontraram ângulo que
  mude a conclusão.

### 4.8 Mudança no regime de abertura (desde out/nov de 2025)
- Dias sem candle de 9:00: 3% em 2024, ~10% em jan-set/2025, **55%** de 2025-11-04 a 2026-09-02
  (1º candle às 9:02 em 18% dos dias e às 9:03 em 35%).
- Nesses dias o 1º candle tem 2 a 3,5 vezes o volume dos candles seguintes e dezenas de milhares
  de negócios: é o print do leilão de abertura. Em 2026 o candle de 9:02 tem range mediano de
  400 pts, 74% do alvo de 0,30% (543 pts).
- Causa provável, **não confirmada em fonte primária** (o proxy bloqueou b3.com.br): Ofícios
  Circulares B3 048/2025-VNC e 056/2025-VNC, que sincronizam os leilões de pré-abertura de
  WIN/IND, WDO/DOL e WSP/ISP com encerramento aleatório, em fases a partir de 24/11/2025. O padrão
  nos dados começa em 2025-10-07.
- Consequência: o resultado de 2026 (82 operações) cobre só os dias que abriram às 9:00. Uma
  variante adaptada (gap pelo 1º candle, entrada no seguinte) nos dias sem 9:00 desde 2025-10-07
  dá +20,9/op com t 0,53: nada, e escolhida depois de ver os dados.

### 4.9 Entrada às 9:15 (`scripts/entrada_0915.py`)
Mesma ideia deslocada: ler 9:00-9:14, entrar na abertura do candle de 9:15, sair no alvo, no stop
ou às 9:30. Regras e grade fixadas antes de rodar (os 6 sinais de sempre, agora com momentum dos
15 minutos, nos 4 pares de alvo/stop, mais o rompimento da faixa de 9:00-9:14 com stop no outro
extremo, alvo de 1x a faixa e saída até 9:59). 3.494 pregões avaliáveis; o candle de 9:15 existe
mesmo nos dias de leilão prolongado. Saída em `resultados/entrada_0915_2012-2026.txt`.

| Regra (custo 10) | n | Média/op | t | 1ª metade | 2ª metade |
|---|---|---|---|---|---|
| Momentum 15 min 0,20/0,20 (a menos ruim) | 3471 | -3,3 | -1,30 | -7,7 | +1,2 |
| Contra o gap 0,30/0,30 | 3366 | -13,0 | -4,53 | -12,7 | -13,2 |
| Reversão 15 min 0,20/0,20 | 3471 | -17,0 | -6,79 | -12,4 | -21,5 |
| Rompimento da faixa | 3040 | -11,8 | -2,58 | -14,0 | -9,6 |
| Cara ou coroa (mediana de 1.000 sorteios) | 3494 | -9,9 | | | |

- Todas as 24 combinações e o rompimento são negativos no período inteiro e em cada metade.
- Sem custo, o único sinal com informação é a continuação dos 15 primeiros minutos: +6,5/op
  (t 2,29; 2ª metade +10,0, t 2,00). Contra o gap sem custo: -3,0. Nada paga 10 pts de custo,
  muito menos os 12 a 40 pts reais.
- Amplitude mediana: 375 pts em 9:00-9:14 e 220 pts em 9:15-9:29; o alvo de 0,30% (~280 pts) é
  maior que a amplitude típica da janela de saída, por isso 2/3 das operações saem por tempo.

---

## 5. Conclusão atual

- **O operacional da imagem não se sustenta.** A regra escolhida em 2012 era ruído de seleção
  entre 24 combinações em 99 dias: fora da amostra não tem edge nem antes dos custos.
- **Nenhuma das 24 combinações** da grade é positiva fora da amostra.
- **Custo real** do WIN hoje (B3 ~2,5 pts ida e volta, corretagem de 0 a 25 pts, slippage de pelo
  menos 1 tick por ponta) fica entre 12 e 40+ pts, acima dos 10 usados no teste; só piora.
- **A janela 9:00-9:02 deixou de existir** em metade dos pregões desde o fim de 2025; qualquer
  operacional de abertura hoje tem que partir do print do leilão.
- **Entrar às 9:15 não resolve:** com leitura de 9:00-9:14, nenhuma regra é positiva (ver 4.9).
- Liquidez não é problema (40 a 90 mil contratos por minuto às 9:05-9:14 em 2025-26).

---

## 6. O que falta (e o que não vale a pena)

Os itens 1 a 5 e 7 a 8 da lista anterior (validação fora da amostra, mais dados, múltiplos testes,
ordem de grandeza dos custos, resultado por ano, walk-forward) foram feitos; ver 4.7 e 4.8.

1. **Regime de abertura.** Ler os Ofícios Circulares B3 048/2025-VNC e 056/2025-VNC (ou a grade
   vigente) para saber a janela de encerramento do leilão de pré-abertura do WIN. Isso muda a
   descrição de qualquer operacional de abertura, não a estatística.
2. **Custos do próprio usuário.** Tabela da corretora (corretagem, RLP) e emolumentos atuais da
   B3, convertidos em pontos.
3. **Hipótese nova, só com pré-registro.** O único ângulo com alguma tração foi "fade do leilão
   prolongado" (dias sem candle de 9:00: gap pelo print do leilão, entrada no candle seguinte):
   +12 a +22 pts/op com t de 0,8 a 1,5, mas todo o ganho vem de 2025-2026 (127 operações) e
   contradiz o que acontece nos dias normais com gap grande. Se for testar, fixar a regra agora e
   usar só dados posteriores a 2026-09.
4. **Não vale a pena:** reotimizar a grade, walk-forward, gestão de risco/sizing, subperíodos
   escolhidos olhando a tabela por ano. Todos foram checados e não mudam a conclusão.

---

## 7. Arquivos no repositório

- `WINFUT_20MB_1.csv` — os dados (parte 1).
- `scripts/abertura.py` — análise completa: janela 9:00–9:15, volume por horário, alvos em
  retrospecto, as 24 combinações de regras e a base aleatória.
- `scripts/robustez.py` — metades do período, custo dobrado, sem os 5 melhores dias, por tamanho
  do gap.
- `scripts/fora_da_amostra.py` — a regra congelada em dados novos (série WIN$N): separa o
  período de 2012, exclui rolagem e buracos, mostra o resultado por ano, o resto da grade e uma
  base aleatória nos mesmos dias.
- `resultados/fora_da_amostra_2012-2026.txt` — saída completa do teste fora da amostra, com o
  sha256 do CSV usado (o CSV de 154 MB não está no repositório).
- `scripts/entrada_0915.py` — a mesma ideia com entrada às 9:15 (leitura 9:00-9:14, saída até
  9:30) mais o rompimento da faixa dos 15 primeiros minutos; `resultados/entrada_0915_2012-2026.txt`
  tem a saída.
- `README.md` — como rodar e premissas.
- `HANDOFF.md` — este arquivo.

Os scripts usam só a biblioteca padrão do Python (sem pandas/numpy).

---

## 8. Como rodar

```bash
# Com o CSV padrão (WINFUT_20MB_1.csv da raiz):
python3 scripts/abertura.py
python3 scripts/robustez.py

# Com outros dados (um ou mais CSVs no formato do Profit, série ajustada WIN$D):
python3 scripts/abertura.py WINFUT_20MB_1.csv WINFUT_20MB_2.csv
python3 scripts/robustez.py dados_2013.csv dados_2014.csv

# Teste fora da amostra (série WIN$N, não ajustada; o arquivo não está no repositório):
python3 scripts/fora_da_amostra.py WINFUT_NA_BMF_I_v6_raw.csv

# Entrada às 9:15 (mesmo arquivo):
python3 scripts/entrada_0915.py WINFUT_NA_BMF_I_v6_raw.csv
```

Arquivos fatiados são unidos automaticamente: um dia cortado entre dois arquivos é remontado,
linhas repetidas de (data, hora) são descartadas e candles de after-market (`<aft> = S`) são
ignorados. `abertura.py` e `robustez.py` não tratam rolagem: use-os só com a série ajustada.
Para repetir o teste fora da amostra em outro arquivo, **não mexer nos parâmetros da regra**.
