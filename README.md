# codex-teste
Repositório para testes com o Codex

## Teste do "operacional de 15 minutos" na abertura do WIN

Scripts em `scripts/` que testam se dá para operar só a janela das 9:00 às 9:15 do WINFUT
(entrada às 9:02, saída no alvo, no stop ou às 9:15) com candles de 1 minuto.
Só usam a biblioteca padrão do Python.

```bash
python3 scripts/abertura.py     # janela 9:00-9:15, volume por horário, regras testadas, base aleatória
python3 scripts/robustez.py     # metades do período, custo maior, sem os 5 melhores dias, tamanho do gap
python3 scripts/fora_da_amostra.py WINFUT_NA_BMF_I_v6_raw.csv   # regra congelada em dados que não foram usados na escolha
```

Sem argumentos, `abertura.py` e `robustez.py` usam `WINFUT_20MB_1.csv`. Para testar outros dados,
passe um ou mais CSVs no mesmo formato de exportação do Profit
(`<ticker>,<date>,<time>,<trades>,<close>,<low>,<high>,<open>,<vol>,<qty>,<aft>`):

```bash
python3 scripts/abertura.py WINFUT_20MB_1.csv WINFUT_20MB_2.csv
```

Arquivos fatiados são unidos: um dia cortado entre dois arquivos é remontado, linhas repetidas
são descartadas e candles de after-market (`<aft>` = `S`) são ignorados.

Premissas do teste:

- A série WIN$D é ajustada multiplicativamente. Os pontos reais são recuperados pelo tamanho do
  tick (5 pts) em cada dia.
- A série WIN$N não é ajustada: no dia de rolagem (quarta-feira mais próxima do dia 15 dos meses
  pares, ou o pregão seguinte) o gap entre o fechamento do contrato velho e a abertura do novo é
  artificial. `fora_da_amostra.py` deixa esses dias sem operação, assim como dias cujo pregão
  anterior está a mais de 5 dias corridos (buraco nos dados). `abertura.py` e `robustez.py` não
  fazem isso: use-os só com a série ajustada.
- Custo de 10 pts por operação (ida e volta), ou 20 pts no teste de robustez.
- Quando stop e alvo caem no mesmo candle de 1 minuto, conta como stop.
- As regras e os alvos/stops foram definidos antes de olhar os resultados, e todas as combinações
  são mostradas. Mesmo assim, com 24 combinações testadas, um t perto de 2 pode sair por acaso.

Com o CSV de 2012 (99 pregões de mai–set), a única regra que se manteve nas duas metades foi
operar contra o gap, com alvo e stop de 0,30%. Testada depois, sem reotimizar, em
`WINFUT_NA_BMF_I_v6_raw.csv` (série WIN$N de 1 minuto, 2012-05-02 a 2026-09-02, 154 MB, não
incluído no repositório), ela não se sustentou: fora da amostra (2012-09-21 a 2026-08-25, 2.921
operações) perdeu 6,9 pts por operação com custo de 10 pts (t = -1,85), teve 5 anos positivos em
15 e, sem custo nenhum, rendeu 3,1 pts por operação (t = 0,83), ou seja, nada. As outras 23
combinações da grade também são negativas fora da amostra. A saída completa está em
`resultados/fora_da_amostra_2012-2026.txt`.

Dois fatos práticos do mesmo arquivo: desde outubro/novembro de 2025, em cerca de metade dos
pregões não há negociação às 9:00 e 9:01 e o primeiro candle aparece às 9:02 ou 9:03 com volume de
leilão, então "ler 9:00-9:02 e entrar às 9:02" não é executável como descrito; e os gaps grandes,
que em 2012 pareciam a melhor parte da regra, são o pior quartil fora da amostra.
