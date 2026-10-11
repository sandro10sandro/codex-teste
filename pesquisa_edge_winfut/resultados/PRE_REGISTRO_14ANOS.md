# Pré-registro do teste de 14 anos — escrito ANTES de rodar (2026-10-11T02:33:11Z)

Dados: WINFUT_NA_BMF_I_v6_raw.csv (WIN$N, 1 minuto, preço real, tick 5), enviado pelo usuário.
sha256 dos dados: 258b23b118fe467e6a0be948cd2d5038fb5f456d4834edc253591b08bd1744b3
Período de teste: 3.434 pregões de 21/09/2012 a 02/09/2026 (os 99 dias anteriores foram usados na
pesquisa e servem só de aquecimento). Nenhum agente viu esses dados. Roda UMA vez.

Hipóteses (9): os 8 candidatos congelados (hash inalterado) + a pista pós-teste (fade 10:05→10:35,
horizonte fixo, sem bracket), cuja regra está em avaliacao/evaluate_14anos.py:pista_trades.

Modo principal "rel": alvo/stop escalados pelo preço (500 = 0,3522% da abertura do dia, mesma proporção
da descoberta), arredondados ao tick. Custos base/stress em ticks como antes (tick = 5 pts).
Estatística principal: t diário do P&L em pontos-base (bps) da abertura do dia, todos os 3.434 dias.

PASSA somente se TODOS:
- P1: total base > 0 e t diário (bps) >= 2,6 (~p unilateral < 0,005 = 0,05/9);
- P2: total com custo stress > 0;
- P3: período recente (01/09/2023 a 02/09/2026) com total base > 0;
- sem uso de dados futuros (lookahead_check).
Descritivo (não decide): modo "fixo" (alvo/stop em pontos reais, ex.: 500 pts), resultado por ano, em R$.
Mesmo que passe: "candidato para simulador (forward test)", não "edge para conta real".

sha256 do código e dos candidatos:
0e2f86b764dc4f6b78eb99b407e49fdf5d501aa5c92960000ffebf577a71b3c8  lib/wf2.py
06d74910663f52b9431370ceafbaa595186c13e10fb9b42ab0e5a8c9e73e96b6  avaliacao/evaluate_14anos.py
9e23cf030781a894197d4e5b1215cde6fa66392b49ef867a2b51809e663d4e88  candidatos/breakout_vol_1.py
d9e90585736b6f414cd052f2980de3ede3438bea7bd74557f0aefc0168bb91cd  candidatos/breakout_vol_2.py
dab7bc4a6376d16bfa67923eb9b7cad2bb48c8a393a06f73b4cf8ced1de717df  candidatos/levels_calendar_1.py
c71757bdc6eb0de84c648491313bdaa8da0115ec1e99435a158015e1009c99ed  candidatos/levels_calendar_2.py
8a2bb479e6b3b8e4df3bf89ad57b67e404b25e6427caff26532b8b20cd018006  candidatos/ml_walkforward_1.py
f267d02a13f729838c5e3354b70c452f1d4f82d8e48b52b2e56984a1b6942ad4  candidatos/time_of_day_1.py
f648895270414b3018060549b3c99b449085a883b90b0229f1341ea578ee66a2  candidatos/time_of_day_2.py
662cf502eebf78fa75a0d75a832e4c6190deb61cc6f94b302c6c1ded7e41a40c  candidatos/volume_flow_1.py
