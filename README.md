# codex-teste
Repositório para testes com o Codex

## Teste do "operacional de 15 minutos" na abertura do WIN

Scripts em `scripts/` que testam se dá para operar só a janela das 9:00 às 9:15 do WINFUT
(entrada às 9:02, saída no alvo, no stop ou às 9:15) com candles de 1 minuto.
Só usam a biblioteca padrão do Python.

```bash
python3 scripts/abertura.py     # janela 9:00-9:15, volume por horário, regras testadas, base aleatória
python3 scripts/robustez.py     # metades do período, custo maior, sem os 5 melhores dias, tamanho do gap
```

Sem argumentos, os dois usam `WINFUT_20MB_1.csv`. Para testar outros dados, passe um ou mais
CSVs no mesmo formato de exportação do Profit
(`<ticker>,<date>,<time>,<trades>,<close>,<low>,<high>,<open>,<vol>,<qty>,<aft>`):

```bash
python3 scripts/abertura.py WINFUT_20MB_1.csv WINFUT_20MB_2.csv
```

Arquivos fatiados são unidos: um dia cortado entre dois arquivos é remontado, linhas repetidas
são descartadas e candles de after-market (`<aft>` = `S`) são ignorados.

Premissas do teste:

- A série WIN$D é ajustada multiplicativamente. Os pontos reais são recuperados pelo tamanho do
  tick (5 pts) em cada dia.
- Custo de 10 pts por operação (ida e volta), ou 20 pts no teste de robustez.
- Quando stop e alvo caem no mesmo candle de 1 minuto, conta como stop.
- As regras e os alvos/stops foram definidos antes de olhar os resultados, e todas as combinações
  são mostradas. Mesmo assim, com 24 combinações testadas, um t perto de 2 pode sair por acaso.

Com o CSV atual (99 pregões de mai–set/2012), a única regra que se manteve nas duas metades foi
operar contra o gap, com alvo e stop de 0,30%. Mesmo ela bateu o alvo em só 32% das operações, e a
maioria saiu por tempo às 9:15. É uma hipótese a validar em dados que ainda não foram olhados, não
um operacional pronto.
