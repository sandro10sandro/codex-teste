# Pesquisa de edge no WINFUT (alvo máx. +500 / stop máx. −500)

**Resultado: nenhum setup sobreviveu fora da amostra.** Foram testadas 21.243 variações.
Saíram 8 candidatos da descoberta. 7 reprovaram na validação. O único que chegou ao teste
final (holdout) ficou no zero a zero.

## Dados

- `../WINFUT_20MB_1.csv`: candles de 1 minuto do WIN$D (série contínua **ajustada**), de 02/05/2012 a 20/09/2012, com 99 pregões.
- Os preços são ajustados. Nenhum fechamento é múltiplo de 5, e o tick real (5 pts) vale ~12,5–12,8 pts nesta série. Por isso 500 pts aqui ≈ 0,32% do preço.
- A divisão é cronológica e foi fixada antes de qualquer teste:

| Período    | Datas                 | Dias | Uso                                     |
|------------|-----------------------|------|-----------------------------------------|
| Descoberta | 02/05 a 25/07/2012    | 59   | única base liberada para procurar setups |
| Validação  | 26/07 a 22/08/2012    | 20   | trancada; só testa candidatos congelados |
| Holdout    | 23/08 a 20/09/2012    | 20   | trancado; máx. 3 candidatos, uma vez     |

## Regras do simulador (`lib/wf.py`)

- O sinal sai no fechamento do candle *i*, e a entrada é a mercado na abertura do candle *i+1*.
- Uma posição por vez. Sem entradas depois das 17:00. Saída forçada no último candle do dia.
- Se alvo e stop cabem no mesmo candle, conta o **stop**.
- Custo "base":
  - 1 tick de slippage na entrada e 1 tick na saída a mercado;
  - 0,5 tick de corretagem e emolumentos;
  - o alvo só é executado se o preço passar 1 tick além dele.
- O custo "stress" dobra tudo.
- O simulador foi conferido contra uma versão força-bruta, com zero divergências.
- Todo candidato passa por um teste que garante que ele não usa dados futuros.

Referência: entradas aleatórias com 500/500 perdem ~30 pts por operação com custo base (acerto de ~48%).

## Processo

1. Seis linhas de busca independentes trabalharam só na descoberta:
   - horário do dia;
   - rompimento e volatilidade;
   - reversão contra momentum;
   - volume e fluxo;
   - níveis de referência e calendário;
   - machine learning walk-forward.

   Ao todo foram **21.243 variações** (`resultados/*_variants.txt`).
2. Filtro da descoberta. O candidato precisava, ao mesmo tempo:
   - lucrar depois dos custos, com t diário ≥ 2 e n ≥ 40;
   - lucrar nas duas metades do período;
   - lucrar com custo stress;
   - ter p < 0,05 contra entradas aleatórias;
   - ter parâmetros vizinhos também lucrativos.

   **8 candidatos** passaram (`candidatos/`).
3. Os critérios de validação e holdout foram escritos **antes** de abrir os dados trancados, com o hash de cada candidato (`resultados/PRE_REGISTRO.md`).

## Resultados (custo base, pts por operação)

| Candidato | Ideia | Descoberta | Validação | Holdout |
|---|---|---|---|---|
| time_of_day_1 | contra o movimento desde a abertura, 10:05–10:29 | +125 (n=110) | +93 (n=48, p=0,022, t diário 1,19) → promissor | **+12** (n=42, p=0,24, t diário 0,13) → **reprovado** |
| time_of_day_2 | mesma ideia, 1 entrada às 10:10 | +202 | +89 (p=0,11) → reprovado | — |
| breakout_vol_1 | fade do 1º rompimento da faixa de 30 min antes das 10h | +194 | −13 → reprovado | — |
| breakout_vol_2 | idem, qualquer horário | +150 | −13 → reprovado | — |
| volume_flow_1 | segue ou faz fade às 9:30 conforme o volume | +162 | −13 → reprovado | — |
| levels_calendar_1 | rompimento da faixa das 9h condicionado ao fechamento anterior | +114 | −87 → reprovado | — |
| levels_calendar_2 | rompimento de máxima/mínima "velha" condicionado ao fechamento anterior | +106 | +33 (p=0,16) → reprovado | — |
| ml_walkforward_1 | regressão logística, fade da abertura | +42 | −5 → reprovado | — |

No holdout, o `time_of_day_1` teve 52% de acerto e só 40% de dias positivos, com drawdown máximo de −3.682 pts. Ficou **negativo com custo stress** (−514 pts) e também perto de zero sem custo (+500 pts em 45 operações).

Integridade:
- Os sinais calculados na série combinada são idênticos aos da série só de descoberta.
- Esta pasta reproduz os resultados de forma idêntica: `python3 avaliacao/evaluate.py validation candidatos/*.py`.

## Verificação adversarial independente

Dois agentes tentaram derrubar a conclusão (`verificacao/`, `resultados/verificacao.json`). **Os dois concluíram que ela se sustenta.**

- **Reimplementação do zero.** O agente escreveu outro carregador e outro simulador sem ver este código. Ele reproduziu até a casa decimal todos os números do `time_of_day_1` nos três períodos.
- **Auditoria de código.** Um simulador independente bateu operação por operação com `wf.backtest`, nos 8 candidatos, nos 3 períodos e nos 3 custos. Nenhum script de exploração leu dados além da descoberta.

Achados, todos sem efeito no veredito:

1. **Cache do simulador.** O cache usava `id()` do DataFrame e poderia devolver resultado velho. Não afetou nenhum número, mas foi corrigido: agora a chave é o hash do conteúdo.
2. **A comparação com entradas aleatórias é otimista.** Ela trata operações do mesmo dia como independentes. Com testes que respeitam o agrupamento por dia, o p da validação do `time_of_day_1` sobe de 0,022 para 0,03–0,12. Ou seja, ele provavelmente nem deveria ter ido ao holdout.
3. **O custo "stress" é brando.** Ele não dobra o tick exigido além do alvo. Dobrando também isso, o holdout cai de −514 para −2.027 pts.
4. **O último dia (20/09/2012) é parcial,** com 35 candles até 9:34. Impacto desprezível.

Sensibilidade a escolhas de implementação: trocar detalhes razoáveis muda o sinal do holdout do `time_of_day_1`. Exemplos:
- bracket calculado a partir da abertura em vez do preço executado: −570;
- reentrada só no candle seguinte à saída: −2.007.

Isso confirma que o resultado fora da amostra é basicamente ruído.

**Ressalva honesta: o poder estatístico é baixo.** Mesmo que o edge da descoberta fosse real, 19–20 dias de holdout só o detectariam em ~33–55% das vezes. Por isso, a leitura correta é:
- **um edge do tamanho que a descoberta mostrava é desfavorecido** (z = −1,26 só no holdout);
- **um edge menor não foi demonstrado** e não dá para demonstrar com estes dados.

**Pista pós-teste (não vale como evidência).** Depois de ver os dados de teste, o reimplementador testou 8 horizontes de saída fixos. Um deles foi: sinal às 10:05, entrada às 10:06, saída às 10:35, sem bracket. Ele foi positivo na validação (t 1,80) e no holdout (t 1,90). Mas:
- o horizonte foi escolhido olhando a resposta;
- sem os 2 melhores dias, o t cai para ~1,0–1,2;
- a versão com bracket 500/500 perdeu nos dois períodos de teste.

No máximo, é uma hipótese para um teste novo, com dados que ninguém viu e regra congelada antes.

## Por que 99 dias não provam edge

Cada operação 500/500 tem desvio de ~500 pts. Para distinguir um edge real de sorte é preciso:

| Edge real por operação | Operações (teste simples) | Operações (corrigido p/ 21 mil testes) |
|---|---|---|
| +30 pts | ~1.070 (~4 anos, 1 por dia) | ~6.200 (~25 anos) |
| +50 pts | ~380 (~1,5 ano) | ~2.200 (~9 anos) |
| +100 pts | ~100 | ~560 (~2 anos) |

Um backtest de poucos meses que "mostra" +150 pts por operação depois de milhares de tentativas é,
quase sempre, sorte selecionada. Foi exatamente o que aconteceu aqui: os resultados da descoberta
(+100 a +200 pts) sumiram nos dados novos.

## O que esta pesquisa NÃO é

- Não é recomendação de operar. Nada aqui deve ir para conta real.
- Mesmo que algo tivesse passado, o rótulo seria "candidato para simulador", não "edge validado". São só 99 dias de 2012, com volatilidade e regras de pregão diferentes das de hoje.

## Estrutura

- `lib/wf.py`: carregador, simulador, comparação com entradas aleatórias, teste de dados futuros.
- `avaliacao/evaluate.py`: avaliação nos períodos trancados.
- `candidatos/`: os 8 candidatos congelados.
- `resultados/`: pré-registro, resultados da descoberta, validação e holdout, contagem de variações.
- `exploracao/`: scripts das linhas de busca, mantidos para auditoria. Usam caminhos absolutos da sessão original e não rodam sem ajuste.
- `verificacao/`: scripts da auditoria e da reimplementação independente. Têm os mesmos caminhos absolutos.
