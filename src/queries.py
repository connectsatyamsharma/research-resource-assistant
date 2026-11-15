"""Evaluation query set: normal, edge and incomplete cases.

gold_themes: a resource (Lab/Dataset/Facility) is judged relevant if it is tagged with any of these themes
             (annotated by the project author from the query intent, BEFORE running the system).
gold_ids:    optional explicit relevant ids (overrides gold_themes).
Empty gold => the system SHOULD abstain / route to human review (out-of-scope or too vague).
"""
QUERIES = [
    # ---- NORMAL (12) ----
    dict(id="N01", kind="normal", q="labs working on tumor detection in MRI scans", gold_themes=["T01"]),
    dict(id="N02", kind="normal", q="datasets for training chatbots in Hindi", gold_themes=["T02"]),
    dict(id="N03", kind="normal", q="where can I test autonomous drone navigation", gold_themes=["T03"]),
    dict(id="N04", kind="normal", q="photovoltaic panel performance data", gold_themes=["T04"]),
    dict(id="N05", kind="normal", q="forecasting monsoon rainfall", gold_themes=["T05"]),
    dict(id="N06", kind="normal", q="DNA sequencing facility for gene expression study", gold_themes=["T06"]),
    dict(id="N07", kind="normal", q="detect malware and network attacks", gold_themes=["T07"]),
    dict(id="N08", kind="normal", q="nanomaterial coatings against corrosion", gold_themes=["T08"]),
    dict(id="N09", kind="normal", q="predict crop disease from leaf photos", gold_themes=["T09"]),
    dict(id="N10", kind="normal", q="traffic congestion prediction using sensors", gold_themes=["T10"]),
    dict(id="N11", kind="normal", q="language models for sentiment analysis on tweets", gold_themes=["T02"]),
    dict(id="N12", kind="normal", q="battery degradation and energy storage", gold_themes=["T04", "T08"]),
    # ---- EDGE: cross-departmental / paraphrased / multi-theme (7) ----
    dict(id="E01", kind="edge", q="AI for crop yield using satellite and weather data", gold_themes=["T09", "T05"]),
    dict(id="E02", kind="edge", q="secure IoT sensor networks in smart cities", gold_themes=["T07", "T10"]),
    dict(id="E03", kind="edge", q="computing resources for training large deep learning models", gold_ids=["F01"]),
    dict(id="E04", kind="edge", q="robots for warehouse logistics and routing", gold_themes=["T03", "T10"]),
    dict(id="E05", kind="edge", q="renewable energy materials research", gold_themes=["T04", "T08"]),
    dict(id="E06", kind="edge", q="protein folding on GPUs", gold_themes=["T06"]),
    dict(id="E07", kind="edge", q="x ray lung scan screening", gold_themes=["T01"]),
    # ---- HARD: vocabulary not present in any record (tests true semantic generalisation) (5) ----
    dict(id="H01", kind="hard", q="tomato blight detection", gold_themes=["T09"]),
    dict(id="H02", kind="hard", q="self-driving vehicle perception", gold_themes=["T03"]),
    dict(id="H03", kind="hard", q="predict electricity demand of the campus", gold_themes=["T04"]),
    dict(id="H04", kind="hard", q="recognise hate speech on social media", gold_themes=["T02"]),
    dict(id="H05", kind="hard", q="ageing of lithium cells", gold_themes=["T04", "T08"]),
    # ---- INCOMPLETE / NOISY / OUT-OF-SCOPE (5) ----
    dict(id="I01", kind="incomplete", q="medcal imagng segmentaton", gold_themes=["T01"]),          # typos
    dict(id="I02", kind="incomplete", q="quantum photonics", gold_ids=["L12"]),                    # record has missing fields
    dict(id="I03", kind="incomplete", q="data", gold_themes=[]),                                   # too vague -> abstain
    dict(id="I04", kind="incomplete", q="blockchain voting system", gold_themes=[]),               # out of scope -> abstain
    dict(id="I05", kind="incomplete", q="", gold_themes=[]),                                       # empty -> abstain
]
