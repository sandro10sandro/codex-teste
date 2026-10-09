# Handoff — Teste do "operacional de 15 minutos" na abertura do WINFUT

Este arquivo passa para outra sessão (ou outra pessoa) **tudo que já foi analisado** e
**tudo que ainda falta analisar** sobre a ideia de operar só a janela das 9:00 às 9:15 do
mini índice (WIN). Ele é autossuficiente: dá para ler só este arquivo e continuar o trabalho.

---

## 0. Prompt pronto para colar numa nova sessão

> Continue a análise descrita em `HANDOFF.md` deste repositório. Já existe o resultado de um
> teste da janela de abertura (9:00–9:15) do WINFUT em `scripts/abertura.py` e
> `scripts/robustez.py`, rodado sobre `WINFUT_20MB_1.csv` (99 pregões de 2012). A regra que
> se sustentou foi "contra o gap" com alvo/stop de 0,30%. O próximo passo mais importante é
> **validação out-of-sample**: rodar essa mesma regra, já congelada, em dados que ainda não
> foram olhados (2013 em diante), sem reotimizar nada. Veja a seção "O que falta analisar"
> para a lista completa. Se houver novos CSVs no formato do Profit, rode os scripts passando
> esses arquivos como argumento.

---

## 1. Contexto e objetivo

A pergunta original: **é possível ter um operacional de ~15 minutos na abertura do WIN**, como
o que circula em imagem de rede social (entra 9:02 com plano, alvo batido 9:12, "dia resolvido
em 15 minutos")?

A abordagem aqui foi: definir regras **antes** de ver os resultados (sem viés de análises
anteriores), testar todas, reportar inclusive as que perderam, e medir se sobra algo depois de
custos e de checagens de robustez.

**Resposta curta:** dá para montar e seguir um operacional de abertura no WIN — há liquidez e a
janela oscila o bastante para um alvo. Mas o que a imagem vende ("alvo batido 9:12 todo dia")
os dados não mostram. Só uma regra sobreviveu às checagens, e mesmo ela bate o alvo em ~1/3 das
vezes; é uma hipótese a validar, não um operacional provado.

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

---

## 5. Conclusão atual

- **Operar a abertura do WIN é viável** em liquidez e volatilidade.
- **A imagem exagera:** "alvo batido 9:12, dia resolvido" não é a rotina; na melhor regra só 1/3
  dos dias bate o alvo e a maioria sai no horário com resultado pequeno.
- **Candidata a edge:** "contra o gap", entrada 9:02, alvo e stop de **0,30%**, saída 9:15.
  ~57% de acerto, ~+32 pts/op (≈ R$ 6,40 por minicontrato/dia antes do IR), sobreviveu às metades,
  ao custo dobrado e à remoção dos melhores dias.
- **Mas NÃO está validada.** Ver seção 6.

---

## 6. O que falta analisar (lista priorizada para a próxima sessão)

1. **[CRÍTICO] Validação out-of-sample.** Rodar a regra "contra o gap 0,30/0,30" **já congelada**
   (sem reotimizar nada) em dados que ainda não foram olhados: 2013 até hoje. Se ela mantiver
   acerto ~55–60% e média positiva líquida de custo, vira evidência de verdade. Se não, era
   overfitting dos 99 dias de 2012.
2. **Mais dados.** O CSV atual é a "parte 1". Juntar as outras partes (WINFUT_20MB_2.csv, …) —
   os scripts já aceitam vários arquivos e remontam dias fatiados.
3. **Risco de múltiplos testes.** Foram 24 combinações (6 regras × 4 pares). Um t≈2 pode sair por
   acaso. Com mais dados, refazer só a regra escolhida corrige isso.
4. **Custo realista de hoje.** Corretagem + emolumentos + slippage reais do WIN atual (não 2012).
   Confirmar se +32 pts/op sobrevive ao custo de verdade.
5. **Mudanças estruturais desde 2012.** Entrada em massa do varejo, HFT, horários da B3, e dados
   macro (IBGE, etc.) saindo às 9:00. Testar se o edge persiste por ano.
6. **Definição do gap ao vivo.** Hoje o script usa (abertura 9:00 vs fechamento do dia anterior).
   Confirmar a fonte de preço no tempo real (ajuste, leilão de abertura).
7. **Gestão.** Drawdown em sequência de dias de gap grande, tamanho de posição, pior sequência de
   perdas, e se o resultado aguenta 1 contrato vs vários.
8. **Walk-forward** se houver anos suficientes (otimiza num período, testa no seguinte, rola).

---

## 7. Arquivos no repositório

- `WINFUT_20MB_1.csv` — os dados (parte 1).
- `scripts/abertura.py` — análise completa: janela 9:00–9:15, volume por horário, alvos em
  retrospecto, as 24 combinações de regras e a base aleatória.
- `scripts/robustez.py` — metades do período, custo dobrado, sem os 5 melhores dias, por tamanho
  do gap.
- `README.md` — como rodar e premissas.
- `HANDOFF.md` — este arquivo.

Ambos os scripts usam só a biblioteca padrão do Python (sem pandas/numpy).

---

## 8. Como rodar

```bash
# Com o CSV padrão (WINFUT_20MB_1.csv da raiz):
python3 scripts/abertura.py
python3 scripts/robustez.py

# Com outros dados (um ou mais CSVs no formato do Profit):
python3 scripts/abertura.py WINFUT_20MB_1.csv WINFUT_20MB_2.csv
python3 scripts/robustez.py dados_2013.csv dados_2014.csv
```

Arquivos fatiados são unidos automaticamente: um dia cortado entre dois arquivos é remontado,
linhas repetidas de (data, hora) são descartadas e candles de after-market (`<aft> = S`) são
ignorados. Para a validação out-of-sample (item 1 da seção 6), basta passar os CSVs novos como
argumento — **não mexer nos parâmetros da regra**.
