# University Research Resource Discovery and Evidence Mapping Assistant

An AI-assisted research-planning tool. A researcher describes a need in plain language; the system searches a
**knowledge network** of labs, datasets, facilities, publications and research themes and returns ranked
recommendations with **relationship paths, supporting publications, confidence, explanations and human-review states**.

**Topics:** semantic network, information retrieval, recommendation, explainable AI.

## Features
- Knowledge graph (networkx) linking Labs, Datasets, Facilities, Publications and Themes across departments.
- Three retrievers compared: keyword baseline (TF-IDF), semantic (LSA + character n-grams), **hybrid** (semantic + graph theme match + availability + department context).
- Confidence score, review state, query-coverage safeguard, handling of empty / vague / out-of-scope / incomplete cases.
- Streamlit UI: recommendations, relationship paths, publications, keyword-vs-hybrid comparison, graph view, human-review log.
- Offline evaluation (Precision@5, Recall@5, MRR, nDCG@5, actionable precision, abstention accuracy, latency) and acceptance tests.

## Prerequisites
Python 3.10+ and pip. No GPU, no external datasets or API keys (the dataset is synthetic and included).

## Installation
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```bash
python -m src.data_builder       # (optional) regenerate data/university_kg.json
python -m src.evaluate           # evaluation -> results/*.csv and results/failures.md
python -m pytest -q              # acceptance tests (or: python tests/test_core.py)
streamlit run app.py             # launch the interface at http://localhost:8501
```

## Project structure
```
app.py                  Streamlit interface
src/data_builder.py     builds the synthetic dataset
src/kg.py               knowledge graph construction, record-quality checks
src/retrieval.py        retrievers, hybrid ranking, confidence, review states, explanations
src/queries.py          evaluation queries (normal / edge / hard / incomplete)
src/evaluate.py         metrics, baseline comparison, failure analysis
tests/test_core.py      acceptance tests
data/university_kg.json dataset
results/                metrics tables and failure analysis
docs/                   assumptions and acceptance criteria
```

## Deployment (Streamlit Community Cloud)
Push to GitHub -> https://share.streamlit.io -> New app -> select the repo, branch `main`, main file `app.py`.

## Notes
All data is synthetic. Recommendations are decision support, not final decisions; items not marked
*Auto-recommended* are meant to be confirmed by a human (the UI logs approve / reject / escalate decisions).
