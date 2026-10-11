# Pré-registro (escrito ANTES de rodar validação/holdout) — 2026-10-11T02:10:03Z
sha256 dos candidatos congelados:
9e23cf030781a894197d4e5b1215cde6fa66392b49ef867a2b51809e663d4e88  candidates/breakout_vol_1.py
d9e90585736b6f414cd052f2980de3ede3438bea7bd74557f0aefc0168bb91cd  candidates/breakout_vol_2.py
dab7bc4a6376d16bfa67923eb9b7cad2bb48c8a393a06f73b4cf8ced1de717df  candidates/levels_calendar_1.py
c71757bdc6eb0de84c648491313bdaa8da0115ec1e99435a158015e1009c99ed  candidates/levels_calendar_2.py
8a2bb479e6b3b8e4df3bf89ad57b67e404b25e6427caff26532b8b20cd018006  candidates/ml_walkforward_1.py
f267d02a13f729838c5e3354b70c452f1d4f82d8e48b52b2e56984a1b6942ad4  candidates/time_of_day_1.py
f648895270414b3018060549b3c99b449085a883b90b0229f1341ea578ee66a2  candidates/time_of_day_2.py
662cf502eebf78fa75a0d75a832e4c6190deb61cc6f94b302c6c1ded7e41a40c  candidates/volume_flow_1.py

Variações testadas na descoberta: 21.243 (soma dos logs das 6 lentes). Candidatos: 8.

VALIDAÇÃO (26/07–22/08/2012, 20 dias, K=8):
- APROVADO: total>0 com custo base, n>=15, p (vs aleatório, 5000 sims) < 0.05/8 = 0.00625, lookahead ok.
- PROMISSOR: total>0 com custo base E com custo stress, p < 0.05 (sem correção), n>=15.
HOLDOUT (23/08–20/09/2012, 20 dias):
- Recebe no máximo 3 candidatos: aprovados primeiro, depois promissores, ordenados pelo p da validação,
  no máximo 1 por lente (variações da mesma ideia não contam como evidência independente).
- PASSA: total>0 com custo base E stress, n>=15, p < 0.05/M (M = nº enviados ao holdout), lookahead ok.
- Mesmo passando: rótulo "candidato para simulador (forward test)", nunca "edge validado".
- Se nenhum for aprovado/promissor na validação, o holdout NÃO é aberto e o resultado é "nenhum edge sobreviveu".
