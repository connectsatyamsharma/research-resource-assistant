# Assumptions, Test Cases and Acceptance Criteria

## Assumptions
- A1. The university data is **synthetic** (12 labs, 14 datasets, 8 facilities, 21 publications, 10 research themes, 8 departments), hand-written for this project. No real institutional data or personal data is used.
- A2. Each resource is tagged with one or more research **themes**. Themes carry alias keywords (e.g. "MRI", "tumor detection") so queries phrased differently can still reach them.
- A3. Availability is one of `available`, `limited`, `unavailable`, or **missing** (unknown). Missing is scored 0.3 (neither trusted nor excluded).
- A4. Only Labs, Datasets and Facilities are *recommended*; Publications are used as *supporting evidence*.
- A5. Relevance ground truth for evaluation is assigned from query intent (theme tags or explicit ids) by the project author before running the system.
- A6. English queries only.

## Representative cases
| Type | Example | Expected behaviour |
|---|---|---|
| Normal | "forecasting monsoon rainfall" | Climate lab, rainfall dataset, weather stations ranked top, high confidence |
| Edge (cross-department) | "secure IoT sensor networks in smart cities" | Resources from CSE and Civil/Electronics both appear; cross-department flag shown |
| Edge (paraphrase) | "x ray lung scan screening" | Chest X-ray resources found although the wording differs |
| Hard (unseen vocabulary) | "tomato blight detection" | Confidence reduced because few query terms are recognised; sent to review |
| Incomplete record | "quantum photonics" | Lab found but flagged *Needs human review* (missing availability and description) |
| Unavailable resource | "gene expression cancer cohort" | Dataset shown as *Blocked - unavailable*, not silently hidden |
| Noisy | "medcal imagng segmentaton" | Typos tolerated; confidence low so review state shown |
| Vague / empty / out-of-scope | "data", "", "blockchain voting system" | No confident recommendation; clear message; human review |

## Acceptance criteria (automated in `tests/test_core.py`)
- AC-1 Normal query returns a relevant resource at rank 1.
- AC-2 Cross-departmental results are flagged when a department context is selected.
- AC-3 Empty, vague and out-of-scope queries never produce an *Auto-recommended* result.
- AC-4 Records with missing fields are routed to *Needs human review* and list the missing fields.
- AC-5 Unavailable resources are shown as *Blocked - unavailable* (with explanation), not hidden.
- AC-6 Every result carries a confidence value in [0,1], a relationship path and a text explanation.
- AC-7 Hybrid retrieval handles a paraphrased query at least as well as the keyword baseline.
- AC-8 (offline) Hybrid nDCG@5 and Precision@5 exceed the keyword baseline on the evaluation set (`python -m src.evaluate`).

## Review states
| State | Rule |
|---|---|
| Auto-recommended | confidence >= 0.60, complete record, availability = available |
| Review recommended | confidence 0.35-0.60, or availability = limited |
| Needs human review | confidence < 0.35, or record has missing fields |
| Blocked - unavailable | availability = unavailable |
