"""Avaliação nos períodos trancados. Uso: python3 evaluate.py {validation|holdout} cand1.py [cand2.py ...]

validation = 26/07/2012 a 22/08/2012 (20 dias); holdout = 23/08/2012 a 20/09/2012 (20 dias).
Os sinais são calculados na série inteira até o fim do período (para ter histórico de aquecimento),
mas só contam entradas dentro do período avaliado.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
import wf  # noqa: E402


def load_candidate(path):
    spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    period, paths = sys.argv[1], sys.argv[2:]
    days = wf.all_days()
    if period == "validation":
        df = wf.build(days[: wf.N_DISC + wf.N_VAL])
        eval_days = days[wf.N_DISC: wf.N_DISC + wf.N_VAL]
    elif period == "holdout":
        df = wf.build(days)
        eval_days = days[wf.N_DISC + wf.N_VAL:]
    else:
        raise SystemExit("period must be validation or holdout")
    results = []
    for p in paths:
        m = load_candidate(p)
        sig = m.signals(df)
        row = dict(file=os.path.basename(p), name=getattr(m, "NAME", ""), target=m.TARGET, stop=m.STOP,
                   lookahead_ok=wf.lookahead_check(m.signals, df))
        for cost in ("zero", "base", "stress"):
            tr, st = wf.backtest(df, sig, m.TARGET, m.STOP, cost, entry_days=eval_days)
            row[cost] = st
            if cost == "base":
                row["baseline"] = wf.random_baseline(df, tr, m.TARGET, m.STOP, cost, n_iter=5000,
                                                     entry_days=eval_days)
        results.append(row)
        print(json.dumps(row), flush=True)


if __name__ == "__main__":
    main()
