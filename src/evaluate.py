"""Compares keyword baseline vs semantic vs hybrid. Run: python -m src.evaluate"""
import math
import time
from pathlib import Path
import pandas as pd

from .queries import QUERIES
from .retrieval import Engine, CONF_MED

K = 5
METHODS = ["keyword", "semantic", "hybrid"]
OUT = Path(__file__).resolve().parents[1] / "results"


def relevant_set(eng, q):
    if q.get("gold_ids"):
        return set(q["gold_ids"])
    gt = set(q.get("gold_themes", []))
    return {n for n in eng.items if gt & set(eng.G.nodes[n].get("themes", []))}


def ndcg(ranked, rel, k=K):
    dcg = sum(1 / math.log2(i + 2) for i, r in enumerate(ranked[:k]) if r in rel)
    idcg = sum(1 / math.log2(i + 2) for i in range(min(len(rel), k)))
    return dcg / idcg if idcg else 0.0


def abstained(results, status):
    """System abstains if it returns nothing, flags too_vague/empty/no_match, or top result is low confidence."""
    return status != "ok" or not results or results[0]["confidence"] < CONF_MED


def run():
    eng = Engine()
    rows, abst = [], []
    for q in QUERIES:
        rel = relevant_set(eng, q) if (q.get("gold_themes") or q.get("gold_ids")) else set()
        for m in METHODS:
            t0 = time.perf_counter()
            res, status = eng.search(q["q"], m, k=K)
            ms = (time.perf_counter() - t0) * 1000
            ranked = [r["id"] for r in res]
            if rel:
                hits = [r for r in ranked[:K] if r in rel]
                actionable = [r for r in hits if eng.G.nodes[r].get("availability") != "unavailable"]
                unavail_top3 = sum(eng.G.nodes[r].get("availability") == "unavailable" for r in ranked[:3])
                rr = next((1 / (i + 1) for i, r in enumerate(ranked) if r in rel), 0.0)
                rows.append(dict(qid=q["id"], kind=q["kind"], query=q["q"], method=m,
                                 precision_at_5=len(hits) / K, recall_at_5=len(hits) / min(len(rel), K) if rel else 0,
                                 mrr=rr, ndcg_at_5=ndcg(ranked, rel), actionable_p5=len(actionable) / K,
                                 unavailable_in_top3=unavail_top3, latency_ms=ms, n_relevant=len(rel)))
            else:
                abst.append(dict(qid=q["id"], query=q["q"], method=m, abstained=abstained(res, status), status=status))
    df, ab = pd.DataFrame(rows), pd.DataFrame(abst)
    OUT.mkdir(exist_ok=True)
    df.to_csv(OUT / "per_query_metrics.csv", index=False)
    ab.to_csv(OUT / "abstention.csv", index=False)

    summ = df.groupby("method")[["precision_at_5", "recall_at_5", "mrr", "ndcg_at_5", "actionable_p5", "unavailable_in_top3", "latency_ms"]].mean().loc[METHODS]
    by_kind = df.groupby(["kind", "method"])[["precision_at_5", "mrr", "ndcg_at_5"]].mean().round(3)
    abs_rate = ab.groupby("method")["abstained"].mean().loc[METHODS]
    summ["abstention_accuracy"] = abs_rate
    summ = summ.round(3)
    summ.to_csv(OUT / "summary_metrics.csv")
    by_kind.to_csv(OUT / "metrics_by_query_kind.csv")

    # failure patterns: hybrid queries below 0.6 nDCG, plus why
    fails = df[(df.method == "hybrid") & (df.ndcg_at_5 < 0.6)]
    lines = ["# Failure analysis (hybrid, nDCG@5 < 0.6)\n"]
    for _, r in fails.iterrows():
        lines.append(f"- **{r.qid}** `{r['query']}` -> P@5={r.precision_at_5:.2f}, nDCG={r.ndcg_at_5:.2f}")
    lines.append("\n# Abstention outcomes (queries with no gold resource)\n")
    for _, r in ab.iterrows():
        lines.append(f"- {r.qid} `{r['query']}` [{r.method}] abstained={r.abstained} status={r.status}")
    (OUT / "failures.md").write_text("\n".join(lines), encoding="utf-8")
    return summ, by_kind, fails, ab


if __name__ == "__main__":
    s, bk, f, a = run()
    print("== Summary (mean over %d answerable queries) ==" % (len(QUERIES) - 3)); import pandas as pd; pd.set_option("display.width",200); pd.set_option("display.max_columns",20); print(s)
    print("\n== By query kind =="); print(bk)
    print("\n== Hybrid failures =="); print(f[["qid", "query", "precision_at_5", "ndcg_at_5"]].to_string(index=False))
    print("\n== Abstention =="); print(a.to_string(index=False))
