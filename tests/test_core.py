"""Acceptance tests (see docs/ASSUMPTIONS_AND_ACCEPTANCE.md). Run: python -m pytest -q   (or python tests/test_core.py)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.retrieval import Engine

eng = Engine()


def top(q, method="hybrid"):
    return eng.search(q, method)


def test_normal_query_top_result_relevant():          # AC-1
    res, status = top("labs working on tumor detection in MRI scans")
    assert status == "ok" and res[0]["id"] in {"L01", "D02", "D01"}


def test_edge_cross_department():                      # AC-2
    res, _ = eng.search("secure IoT sensor networks in smart cities", k=5, context_dept="CSE")
    assert any(r["cross_department"] for r in res)


def test_empty_and_vague_queries_abstain():            # AC-3
    assert top("")[1] == "empty_query"
    assert top("data")[1] == "too_vague"


def test_out_of_scope_is_not_confident():              # AC-3
    res, status = top("blockchain voting system")
    assert status == "no_match" and all(r["state"] == "Needs human review" for r in res)


def test_incomplete_record_goes_to_human_review():     # AC-4
    res, _ = top("quantum photonics")
    l12 = next(r for r in res if r["id"] == "L12")
    assert l12["state"] == "Needs human review" and "availability" in l12["missing_fields"]


def test_unavailable_resource_is_blocked_not_hidden():  # AC-5
    res, _ = eng.search("gene expression cancer cohort", k=10)
    d11 = [r for r in res if r["id"] == "D11"]
    assert d11 and d11[0]["state"] == "Blocked - unavailable"


def test_every_result_has_explanation_and_confidence():  # AC-6
    res, _ = top("predict crop disease from leaf photos")
    for r in res:
        assert 0 <= r["confidence"] <= 1 and r["explanation"] and r["path"]


def test_hybrid_beats_keyword_on_paraphrase():          # AC-7
    kw, _ = top("x ray lung scan screening", "keyword")
    hy, _ = top("x ray lung scan screening", "hybrid")
    assert hy[0]["id"] in {"D01", "L01"}
    assert len(hy) >= len(kw)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("PASS", name)
