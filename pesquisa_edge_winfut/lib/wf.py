"""Biblioteca comum da pesquisa de edge no WINFUT (WIN$D, candles de 1 minuto).

Regras fixas da pesquisa:
- Alvo e stop medidos em pontos da SÉRIE AJUSTADA do arquivo (500 pts ~ 0,32% do preço).
  O tick real (5 pts) vale ~12,5 a 12,8 pts nesta série; a coluna `tick` traz o valor do dia.
- Sinal calculado no FECHAMENTO do candle i; entrada a mercado na ABERTURA do candle i+1.
- Sem entradas depois das 17:00. Saída forçada no fechamento do último candle do dia.
- Uma posição por vez por estratégia (sinais durante uma operação aberta são ignorados).
- Se alvo e stop cabem no mesmo candle, conta o STOP (conservador).
- Custos "base": 1 tick de slippage na entrada, 1 tick na saída a mercado (stop/fim do dia),
  0,5 tick de corretagem+emolumentos; alvo (ordem limitada) só conta se o preço passar
  1 tick além dele. "stress" dobra tudo. "zero" não tem custo e alvo conta no toque.

Uso:
    from wf import load, backtest, random_baseline, lookahead_check
    df = load()                      # só o período de DESCOBERTA
    sig = [(i, +1), (j, -1)]         # (índice do candle de sinal, direção)
    trades, st = backtest(df, sig, target=500, stop=500, cost="base")
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd

RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "WINFUT_20MB_1.csv")
N_DISC, N_VAL = 59, 20          # 59 dias descoberta, 20 validação, 20 holdout (trancado)
NO_ENTRY_AFTER = 170000
TARGETS = (200, 300, 400, 500)  # alvo máximo 500
STOPS = (200, 300, 400, 500)    # stop máximo 500
COSTS = {
    "zero":   dict(entry=0.0, exit=0.0, fee=0.0, through=0.0),
    "base":   dict(entry=1.0, exit=1.0, fee=0.5, through=1.0),
    "stress": dict(entry=2.0, exit=2.0, fee=1.0, through=1.0),
}


def _raw() -> pd.DataFrame:
    df = pd.read_csv(RAW)
    df.columns = [c.strip("<>") for c in df.columns]
    return df


def all_days() -> list[int]:
    return sorted(_raw()["date"].unique().tolist())


def build(days: list[int]) -> pd.DataFrame:
    """Monta o DataFrame padrão para uma lista de dias (uso interno)."""
    df = _raw()
    df = df[df["date"].isin(days)].copy()
    df["dt"] = pd.to_datetime(df["date"].astype(str) + df["time"].astype(str).str.zfill(6),
                              format="%Y%m%d%H%M%S")
    df = df.sort_values("dt").reset_index(drop=True)
    df["mod"] = (df["dt"].dt.hour - 9) * 60 + df["dt"].dt.minute     # minutos desde 9:00
    df["dow"] = df["dt"].dt.dayofweek                                  # 0=segunda
    day_ids = {d: k for k, d in enumerate(sorted(df["date"].unique()))}
    df["day"] = df["date"].map(day_ids)
    # tick do dia = menor diferença positiva entre preços do dia (= 5 pts reais)
    ticks = {}
    for d, g in df.groupby("date"):
        px = np.unique(np.round(np.concatenate([g[c].values for c in ("open", "high", "low", "close")]), 4))
        diffs = np.diff(px)
        diffs = diffs[diffs > 1e-6]
        ticks[d] = float(np.round(diffs.min(), 4)) if len(diffs) else np.nan
    df["tick"] = df["date"].map(ticks)
    df["tick"] = df["tick"].fillna(df["tick"].median())
    f = df["tick"] / 5.0                                              # pts ajustados por pt real
    for c in ("open", "high", "low", "close"):
        df["real_" + c] = df[c] / f                                    # preço real aproximado
    df["first_of_day"] = df["day"].ne(df["day"].shift())
    df["last_of_day"] = df["day"].ne(df["day"].shift(-1))
    return df[["dt", "date", "time", "mod", "dow", "day", "open", "high", "low", "close",
               "trades", "qty", "vol", "tick", "real_open", "real_high", "real_low",
               "real_close", "first_of_day", "last_of_day"]]


def load() -> pd.DataFrame:
    """Período de DESCOBERTA (02/05/2012 a 25/07/2012). Única base liberada para explorar."""
    return build(all_days()[:N_DISC])


# ---------------------------------------------------------------- resultado de cada entrada
_CACHE: dict = {}


def outcomes(df: pd.DataFrame, target: float, stop: float, cost: str = "base"):
    """Para cada candle e (entrada na abertura dele) e direção: pnl em pts, candle de saída, tipo.

    Retorna dict {+1: (pnl, exit_idx, kind), -1: (...)}; kind: 1=alvo, -1=stop, 0=fim do dia.
    """
    if target > 500 or stop > 500:
        raise ValueError("alvo e stop máximos são 500 pts")
    key = (id(df), len(df), float(df["close"].iloc[0]), float(df["close"].iloc[-1]), target, stop, cost)
    if key in _CACHE:
        return _CACHE[key]
    c = COSTS[cost]
    o, h, l, cl = (df[k].values for k in ("open", "high", "low", "close"))
    tk = df["tick"].values
    day = df["day"].values
    n = len(df)
    res = {}
    for d in (1, -1):
        pnl = np.full(n, np.nan)
        ex = np.full(n, -1, dtype=np.int64)
        kind = np.zeros(n, dtype=np.int64)
        starts = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
        ends = np.r_[starts[1:], n]
        for s, e in zip(starts, ends):
            m = e - s
            O, H, L, C, T = o[s:e], h[s:e], l[s:e], cl[s:e], tk[s:e]
            fill = O + d * c["entry"] * T                     # preço de entrada com slippage
            if d == 1:
                tgt = fill + target + c["through"] * T
                stp = fill - stop
                hit_t = H[None, :] >= tgt[:, None]
                hit_s = L[None, :] <= stp[:, None]
            else:
                tgt = fill - target - c["through"] * T
                stp = fill + stop
                hit_t = L[None, :] <= tgt[:, None]
                hit_s = H[None, :] >= stp[:, None]
            tri = np.triu(np.ones((m, m), dtype=bool))
            hit_t &= tri
            hit_s &= tri
            ft = np.where(hit_t.any(1), hit_t.argmax(1), m)
            fs = np.where(hit_s.any(1), hit_s.argmax(1), m)
            for i in range(m):
                if fs[i] <= ft[i] and fs[i] < m:           # stop (inclusive empate)
                    j = fs[i]
                    stop_px = fill[i] - d * stop
                    px = min(stop_px, O[j]) if d == 1 else max(stop_px, O[j])
                    if j == i:
                        px = stop_px
                    px -= d * c["exit"] * T[j]
                    k = -1
                elif ft[i] < m:
                    j = ft[i]
                    px = fill[i] + d * target
                    k = 1
                else:
                    j = m - 1
                    px = C[j] - d * c["exit"] * T[j]
                    k = 0
                pnl[s + i] = d * (px - fill[i]) - c["fee"] * T[i]
                ex[s + i] = s + j
                kind[s + i] = k
        res[d] = (pnl, ex, kind)
    _CACHE[key] = res
    return res


def backtest(df: pd.DataFrame, signals, target: float = 500, stop: float = 500,
             cost: str = "base", entry_days=None):
    """Simula a lista de sinais [(idx_candle_sinal, dir)]. entry_days restringe as entradas
    a certos valores de df['date'] (usado na validação/holdout)."""
    out = outcomes(df, target, stop, cost)
    day = df["day"].values
    tm = df["time"].values
    dates = df["date"].values
    n = len(df)
    allowed = None if entry_days is None else set(entry_days)
    sigs = sorted({(int(i), int(d)) for i, d in signals if d in (1, -1)})
    rows, busy_until = [], -1
    for i, d in sigs:
        e = i + 1
        if e >= n or day[e] != day[i] or tm[e] > NO_ENTRY_AFTER or e <= busy_until:
            continue
        if allowed is not None and dates[e] not in allowed:
            continue
        pnl, ex, kind = out[d]
        rows.append(dict(signal=i, entry=e, exit=int(ex[e]), dir=d, pnl=float(pnl[e]),
                         kind=int(kind[e]), date=int(dates[e]), time=int(tm[e])))
        busy_until = int(ex[e])
    trades = pd.DataFrame(rows, columns=["signal", "entry", "exit", "dir", "pnl", "kind", "date", "time"])
    return trades, stats(trades, df if entry_days is None else df[df["date"].isin(allowed)])


def stats(trades: pd.DataFrame, df: pd.DataFrame | None = None) -> dict:
    if trades.empty:
        return dict(n=0)
    p = trades["pnl"]
    eq = p.cumsum()
    dd = float((eq - eq.cummax()).min())
    gains, losses = p[p > 0].sum(), -p[p < 0].sum()
    days = sorted(df["date"].unique()) if df is not None else sorted(trades["date"].unique())
    daily = trades.groupby("date")["pnl"].sum().reindex(days, fill_value=0.0)
    half = len(days) // 2
    st = dict(
        n=int(len(p)), win_rate=round(float((p > 0).mean()), 4), avg=round(float(p.mean()), 2),
        total=round(float(p.sum()), 1), profit_factor=round(float(gains / losses), 3) if losses > 0 else None,
        max_dd=round(dd, 1),
        t_trade=round(float(p.mean() / (p.std(ddof=1) / np.sqrt(len(p)))), 2) if len(p) > 1 and p.std() > 0 else None,
        days=len(days), pct_days_pos=round(float((daily > 0).mean()), 3),
        t_daily=round(float(daily.mean() / (daily.std(ddof=1) / np.sqrt(len(daily)))), 2) if daily.std() > 0 else None,
        first_half_total=round(float(daily.iloc[:half].sum()), 1),
        second_half_total=round(float(daily.iloc[half:].sum()), 1),
        long_n=int((trades["dir"] == 1).sum()), long_total=round(float(p[trades["dir"] == 1].sum()), 1),
        short_n=int((trades["dir"] == -1).sum()), short_total=round(float(p[trades["dir"] == -1].sum()), 1),
        targets=int((trades["kind"] == 1).sum()), stops=int((trades["kind"] == -1).sum()),
        eod=int((trades["kind"] == 0).sum()),
    )
    return st


def random_baseline(df: pd.DataFrame, trades: pd.DataFrame, target: float = 500, stop: float = 500,
                    cost: str = "base", n_iter: int = 2000, seed: int = 7, entry_days=None) -> dict:
    """Compara com entradas ALEATÓRIAS no mesmo horário (faixas de 30 min) e mesma direção.
    p_value = fração das simulações aleatórias com total >= total da estratégia."""
    if trades.empty:
        return dict(p_value=None)
    out = outcomes(df, target, stop, cost)
    rng = np.random.default_rng(seed)
    bucket = (df["mod"].values // 30)
    ok = (df["time"].values <= NO_ENTRY_AFTER) & ~df["first_of_day"].values
    if entry_days is not None:
        ok &= df["date"].isin(set(entry_days)).values
    pools = {}
    for b in np.unique(bucket):
        pools[b] = np.flatnonzero(ok & (bucket == b))
    sims = np.zeros(n_iter)
    for _, t in trades.iterrows():
        pool = pools.get(bucket[int(t["entry"])])
        if pool is None or len(pool) == 0:
            pool = np.flatnonzero(ok)
        pick = rng.choice(pool, size=n_iter)
        sims += out[int(t["dir"])][0][pick]
    actual = float(trades["pnl"].sum())
    return dict(p_value=round(float((sims >= actual).mean()), 4), actual=round(actual, 1),
                random_mean=round(float(sims.mean()), 1), random_p95=round(float(np.percentile(sims, 95)), 1))


def lookahead_check(signals_fn, df: pd.DataFrame, n_cuts: int = 12, seed: int = 3) -> bool:
    """True se os sinais até o candle t forem iguais rodando com dados só até t (sem olhar o futuro)."""
    rng = np.random.default_rng(seed)
    full = {(int(i), int(d)) for i, d in signals_fn(df)}
    cuts = rng.choice(np.arange(len(df) // 10, len(df) - 1), size=n_cuts, replace=False)
    for t in sorted(cuts):
        part = {(int(i), int(d)) for i, d in signals_fn(df.iloc[: t + 1].copy())}
        if part != {s for s in full if s[0] <= t}:
            return False
    return True


def log_variants(lens: str, k: int) -> None:
    """Registra quantas variações foram testadas (para corrigir comparações múltiplas)."""
    path = os.path.join(os.path.dirname(__file__), "..", "resultados", f"{lens}_variants.txt")
    with open(path, "a") as fh:
        fh.write(f"{k}\n")
