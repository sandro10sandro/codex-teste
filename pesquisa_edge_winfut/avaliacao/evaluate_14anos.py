"""Teste único dos candidatos congelados em 14 anos de dados novos (ver resultados/PRE_REGISTRO_14ANOS.md).

Uso: python3 evaluate_14anos.py <WINFUT_NA_BMF_I_v6_raw.csv> <saida.jsonl> candidatos/*.py

Período de teste: todos os pregões depois de 20/09/2012 (os 99 dias anteriores foram usados na pesquisa
e servem só de aquecimento). Série WIN$N com preço real: tick = 5 pts.
Modo "rel" (principal): alvo/stop do candidato escalados pelo preço, 500 -> 0,3522% da abertura do dia
(mesma proporção da descoberta: 500 / 141.945,9). Modo "fixo" (descritivo): alvo/stop em pontos reais.
"""
import importlib.util
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
import wf2  # noqa: E402

REF = 141945.9           # preço médio ajustado na descoberta: 500 pts = 0,3522%
LAST_RESEARCH_DAY = 20120920
RECENT_FROM = 20230901
T_CRIT = 2.6             # ~p unilateral < 0,005 (Bonferroni para 9 hipóteses)


def load_candidate(path):
    spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def daily_stats(pnl_by_day: pd.Series, days) -> dict:
    s = pnl_by_day.reindex(days, fill_value=0.0)
    sd = s.std(ddof=1)
    return dict(total=round(float(s.sum()), 1), mean=round(float(s.mean()), 3),
                t_daily=round(float(s.mean() / (sd / np.sqrt(len(s)))), 2) if sd > 0 else None,
                pct_days_pos=round(float((s[s != 0] > 0).mean()), 3) if (s != 0).any() else None,
                days=len(s), active_days=int((s != 0).sum()))


def summarize(trades: pd.DataFrame, day_open: pd.Series, days, recent_days) -> dict:
    if trades.empty:
        return dict(n=0)
    t = trades.copy()
    t["bps"] = t["pnl"] / t["date"].map(day_open) * 1e4
    out = dict(n=int(len(t)), win_rate=round(float((t["pnl"] > 0).mean()), 4),
               avg_pts=round(float(t["pnl"].mean()), 2), total_pts=round(float(t["pnl"].sum()), 1),
               total_brl_1contrato=round(float(t["pnl"].sum() * 0.20), 2),
               avg_bps=round(float(t["bps"].mean()), 3))
    out["bps"] = daily_stats(t.groupby("date")["bps"].sum(), days)
    out["pts"] = daily_stats(t.groupby("date")["pnl"].sum(), days)
    rec = t[t["date"].isin(set(recent_days))]
    out["recent"] = dict(n=int(len(rec)), total_pts=round(float(rec["pnl"].sum()), 1),
                         total_bps=round(float(rec["bps"].sum()), 1),
                         win_rate=round(float((rec["pnl"] > 0).mean()), 4) if len(rec) else None)
    out["by_year_bps"] = {int(y): round(float(v), 1) for y, v in t.groupby(t["date"] // 10000)["bps"].sum().items()}
    out["by_year_pts"] = {int(y): round(float(v), 1) for y, v in t.groupby(t["date"] // 10000)["pnl"].sum().items()}
    return out


def pista_trades(df: pd.DataFrame, cost: str, days) -> pd.DataFrame:
    """Pista pós-teste (pré-registrada aqui): no fechamento do candle das 10:05, compara com a abertura
    do candle das 09:00; entra contra o movimento na abertura do candle seguinte; sai no fechamento
    do último candle <= 10:35. Sem bracket. Custos em ticks como no wf2 (entrada, saída, taxa)."""
    c = wf2.COSTS[cost]
    tm, day, date = df["time"].values, df["day"].values, df["date"].values
    o, cl, tk = df["open"].values, df["close"].values, df["tick"].values
    allowed = set(days)
    rows = []
    starts = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
    ends = np.r_[starts[1:], len(df)]
    for s, e in zip(starts, ends):
        if date[s] not in allowed or tm[s] != 90000:
            continue
        sig = np.flatnonzero(tm[s:e] == 100500)
        if len(sig) == 0:
            continue
        i = s + int(sig[0])
        en = i + 1
        ex_c = np.flatnonzero(tm[s:e] <= 103500)
        if en >= e or len(ex_c) == 0:
            continue
        ex = s + int(ex_c[-1])
        if ex <= en:
            continue
        mv = cl[i] - o[s]
        if mv == 0:
            continue
        d = -1 if mv > 0 else 1
        fill = o[en] + d * c["entry"] * tk[en]
        px = cl[ex] - d * c["exit"] * tk[ex]
        rows.append(dict(date=int(date[s]), dir=d, pnl=float(d * (px - fill) - c["fee"] * tk[en])))
    return pd.DataFrame(rows, columns=["date", "dir", "pnl"])


def verdict(base: dict, stress: dict, lookahead_ok=True) -> dict:
    p1 = base.get("n", 0) > 0 and base["bps"]["total"] > 0 and (base["bps"]["t_daily"] or 0) >= T_CRIT
    p2 = stress.get("n", 0) > 0 and stress["bps"]["total"] > 0
    p3 = base.get("n", 0) > 0 and base["recent"]["total_bps"] > 0
    return dict(P1_lucro_e_t=bool(p1), P2_stress=bool(p2), P3_recente=bool(p3), lookahead_ok=bool(lookahead_ok),
                PASSA=bool(p1 and p2 and p3 and lookahead_ok))


def main():
    raw, out_path, paths = sys.argv[1], sys.argv[2], sys.argv[3:]
    wf2.RAW = raw
    wf2.FIXED_TICK = 5.0
    days = wf2.all_days()
    test_days = [d for d in days if d > LAST_RESEARCH_DAY]
    recent_days = [d for d in test_days if d >= RECENT_FROM]
    df = wf2.build(days)
    day_open = df.groupby("date")["open"].first()
    df_rel = df.copy()
    df_rel["bscale"] = df["date"].map(day_open).values / REF
    fh = open(out_path, "w")
    for p in paths:
        m = load_candidate(p)
        sig = m.signals(df)
        la = wf2.lookahead_check(m.signals, df)
        row = dict(file=os.path.basename(p), name=getattr(m, "NAME", ""), target=m.TARGET, stop=m.STOP,
                   lookahead_ok=la)
        for mode, frame in (("rel", df_rel), ("fixo", df)):
            for cost in ("base", "stress", "zero"):
                tr, _ = wf2.backtest(frame, sig, m.TARGET, m.STOP, cost, entry_days=test_days)
                row[f"{mode}_{cost}"] = summarize(tr, day_open, test_days, recent_days)
        row["verdict"] = verdict(row["rel_base"], row["rel_stress"], la)
        print(json.dumps(row), file=fh, flush=True)
        print(row["file"], row["verdict"], flush=True)
    row = dict(file="pista_fade_1005_1035", name="pista pós-teste (horizonte fixo)", target=None, stop=None)
    for cost in ("base", "stress", "zero"):
        row[f"rel_{cost}"] = summarize(pista_trades(df, cost, test_days), day_open, test_days, recent_days)
    row["verdict"] = verdict(row["rel_base"], row["rel_stress"])
    print(json.dumps(row), file=fh, flush=True)
    print(row["file"], row["verdict"], flush=True)
    fh.close()


if __name__ == "__main__":
    main()
